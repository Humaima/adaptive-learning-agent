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
        method="json_schema",
        # Non-strict json_schema mode on gpt-oss-120b intermittently echoes the JSON
        # schema itself before/instead of the actual answer, or otherwise fails to
        # parse — silently yielding parsed=None rather than raising. strict=True uses
        # constrained decoding and reliably returns clean data only.
        strict=True,
        include_raw=include_raw,
    )

    @retry(
        stop=stop_after_attempt(LLM_MAX_RETRIES),
        wait=wait_exponential(min=LLM_RETRY_MIN_WAIT, max=LLM_RETRY_MAX_WAIT),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _call():
        result = structured_llm.invoke(prompt)
        # With include_raw=True a failed parse comes back as {"parsed": None, ...}
        # instead of raising — turn that into a real exception so retry actually
        # retries it, and so a final failure is a loud error, not a silent None.
        if include_raw and isinstance(result, dict) and result.get("parsed") is None:
            raise ValueError(
                f"Structured output failed to parse into {schema!r}: "
                f"{result.get('parsing_error')!r}"
            )
        return result

    return _call()