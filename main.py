import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    reasoning_effort="medium",   # "low" | "medium" | "high" — higher = better reasoning, slower/costlier
    reasoning_format="hidden",    # "hidden" = clean final answer only; "parsed" = separates reasoning from answer
    api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
)

response = llm.invoke("Say 'setup successful' if you can read this.")
print(response.content)