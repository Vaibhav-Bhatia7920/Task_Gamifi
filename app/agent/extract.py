import io
import re
from typing import Optional, Tuple

from pypdf import PdfReader

from app.config import TAVILY_API_KEY

MAX_STORED_CHARS = 200_000
MAX_MODEL_CHARS = 16_000
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


def looks_like_url(value: str) -> bool:
    return bool(URL_RE.match((value or "").strip()))


def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages).strip()


def clip(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


async def tavily_search(query: str) -> str:
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set in app/.env")

    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
    data = await client.search(query, max_results=5)
    chunks = []
    for result in data.get("results") or []:
        title = result.get("title") or ""
        url = result.get("url") or ""
        content = result.get("content") or ""
        chunks.append(f"{title}\n{url}\n{content}".strip())
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


async def tavily_extract(url: str) -> str:
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set in app/.env")

    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
    data = await client.extract(url)
    chunks = []
    for result in data.get("results") or []:
        url_value = result.get("url") or url
        content = result.get("raw_content") or result.get("content") or ""
        chunks.append(f"{url_value}\n{content}".strip())
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


async def gather_source_material(
    raw_data: Optional[str] = None,
    topic: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
) -> Tuple[str, str]:
    """Return (extracted_content, extract_source)."""
    if pdf_bytes:
        extracted = extract_pdf_text(pdf_bytes)
        if extracted:
            return clip(extracted, MAX_STORED_CHARS), "pdf"

    raw = (raw_data or "").strip()
    topic_text = (topic or "").strip()

    if looks_like_url(raw):
        extracted = await tavily_extract(raw)
        if extracted:
            return clip(extracted, MAX_STORED_CHARS), "web"
    if looks_like_url(topic_text):
        extracted = await tavily_extract(topic_text)
        if extracted:
            return clip(extracted, MAX_STORED_CHARS), "web"

    query = topic_text or raw
    if query and TAVILY_API_KEY:
        extracted = await tavily_search(query)
        if extracted:
            if raw and topic_text and raw != extracted:
                extracted = f"{raw}\n\n{extracted}"
            return clip(extracted, MAX_STORED_CHARS), "web"

    if raw:
        return clip(raw, MAX_STORED_CHARS), "user"

    return "", "system"
