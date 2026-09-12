from typing import Any, Dict, List, Optional, Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import OPENAI_API_KEY, OPENAI_MODEL

T = TypeVar("T", bound=BaseModel)

SYSTEM_PROMPT = (
    "You are the Task Gamifi assistant. Be concise. "
    "Use tools when they help you answer accurately."
)

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Return the current UTC time in ISO-8601 format.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    }
]


def require_openai_key() -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in app/.env")
    return OPENAI_API_KEY


def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=require_openai_key())


async def call_llm(
    client: AsyncOpenAI,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
) -> Any:
    return await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=tools if tools is not None else TOOLS,
    )


async def call_structured(
    messages: List[Dict[str, Any]],
    response_model: Type[T],
) -> T:
    client = get_client()
    completion = await client.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=messages,
        response_format=response_model,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        refusal = completion.choices[0].message.refusal or "LLM returned no structured output"
        raise RuntimeError(refusal)
    return parsed
