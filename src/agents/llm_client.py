import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import LLM_MAX_RETRIES, LLM_RETRY_MIN_WAIT, LLM_RETRY_MAX_WAIT

load_dotenv()


def get_groq_llm(reasoning_effort: str = "medium", temperature: float = 0.0) -> ChatGroq:
    """Shared factory — every agent node builds its LLM through this."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=temperature,
        reasoning_effort=reasoning_effort,
        reasoning_format="hidden",
        api_key=SecretStr(groq_api_key) if groq_api_key is not None else None,
    )


def with_structured_output_retry(llm: ChatGroq, schema, prompt: str, include_raw: bool = True):
    """Wraps a structured-output call with exponential-backoff retry —
    Groq's rate limits mean bursts of agent calls (Assessment -> Tutor -> Quiz -> Evaluator)
    can hit 429s in normal use, not just under heavy load."""

    structured_llm = llm.with_structured_output(
        schema,
        method="json_schema",  # explicit — avoids the strict=True default bug on gpt-oss-120b
        include_raw=include_raw,
    )

    @retry(
        stop=stop_after_attempt(LLM_MAX_RETRIES),
        wait=wait_exponential(min=LLM_RETRY_MIN_WAIT, max=LLM_RETRY_MAX_WAIT),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call():
        return structured_llm.invoke(prompt)

    return _call()