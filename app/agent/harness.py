from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.core import call_structured
from app.agent.extract import MAX_MODEL_CHARS, clip, gather_source_material
from app.agent.schemas import CompiledTimeline, RewardsPlan, StructuredContent, TimelinePlan

DEFAULT_RAW_DATA = (
    "I want to ship a small personal project but I keep stalling. "
    "The idea is fuzzy, coding sessions are messy, I skip testing, "
    "and I never share the work. Turn this into a path I can actually follow."
)


def checkpoint_count_for_difficulty(score: int) -> int:
    """Map overall difficulty 0-100 to checkpoint count."""
    if score <= 25:
        return 5
    if score <= 50:
        return 10
    if score <= 75:
        return 15
    return 20


class PipelineState(TypedDict):
    raw_data: str
    source: str
    extracted_content: str
    difficulty_score: int
    structured: Dict[str, Any]
    timeline: Dict[str, Any]
    rewards: Dict[str, Any]
    compiled: Dict[str, Any]


async def structure_node(state: PipelineState) -> Dict[str, Any]:
    material = clip(state.get("extracted_content") or state["raw_data"], MAX_MODEL_CHARS)
    structured = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You structure extracted source material into a clean learning/task brief. "
                    "Keep the source intent. Do not invent a different topic. "
                    "Rate overall difficulty from 0 (trivial for a beginner) to 100 "
                    "(expert / research-level). Use the extracted content, not guesses."
                ),
            },
            {
                "role": "user",
                "content": material or state["raw_data"],
            },
        ],
        StructuredContent,
    )
    payload = structured.model_dump()
    return {
        "structured": payload,
        "difficulty_score": int(structured.difficulty_score),
    }


async def timeline_node(state: PipelineState) -> Dict[str, Any]:
    score = int(state.get("difficulty_score") or 0)
    checkpoint_count = checkpoint_count_for_difficulty(score)
    source_material = clip(
        state.get("extracted_content") or state.get("raw_data") or "",
        MAX_MODEL_CHARS,
    )
    timeline = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You build a gamified learning timeline as ordered checkpoints. "
                    f"You MUST create exactly {checkpoint_count} checkpoints. "
                    "Break the fetched source material into those checkpoints. "
                    "Sort checkpoints from easiest topics first to hardest last. "
                    "Each checkpoint needs: title, lesson content, objective, difficulty "
                    "(easy/medium/hard), and exactly 10 multiple-choice questions "
                    "that test only that checkpoint's content. "
                    "Questions are used to measure progress after the user finishes the content. "
                    "Do not invent a different subject than the source material."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Required checkpoint count: {checkpoint_count}\n"
                    f"Overall difficulty score: {score}/100\n\n"
                    f"Structured brief:\n{state['structured']}\n\n"
                    f"Fetched source material:\n{source_material}"
                ),
            },
        ],
        TimelinePlan,
    )
    payload = timeline.model_dump()
    payload["checkpoint_count"] = checkpoint_count
    return {"timeline": payload}


async def accountant_node(state: PipelineState) -> Dict[str, Any]:
    rewards = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You are the accountant. Assign points and a short reward name "
                    "to every level and every task. Harder work must be worth more points. "
                    "Match task_title to the timeline task titles. "
                    "total_points must equal the sum of all task points."
                ),
            },
            {
                "role": "user",
                "content": f"Assign rewards for this timeline:\n{state['timeline']}",
            },
        ],
        RewardsPlan,
    )
    return {"rewards": rewards.model_dump()}


async def reviewer_node(state: PipelineState) -> Dict[str, Any]:
    compiled = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You are the reviewer. Merge the structured brief, timeline levels, "
                    "and accountant rewards into one final compiled timeline. "
                    "Keep difficulty_score as an integer from 0 to 100. "
                    "Fix missing points, mismatched task names, and unfair rewards. "
                    "Approve only if the path is coherent from start to finish."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Structured:\n{state['structured']}\n\n"
                    f"Timeline:\n{state['timeline']}\n\n"
                    f"Rewards:\n{state['rewards']}\n\n"
                    f"Difficulty score: {state.get('difficulty_score', 0)}/100"
                ),
            },
        ],
        CompiledTimeline,
    )
    payload = compiled.model_dump()
    return {
        "compiled": payload,
        "difficulty_score": int(compiled.difficulty_score or state.get("difficulty_score") or 0),
    }


def build_harness():
    graph = StateGraph(PipelineState)
    graph.add_node("structure", structure_node)
    graph.add_node("timeline", timeline_node)
    graph.add_node("accountant", accountant_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_edge(START, "structure")
    graph.add_edge("structure", "timeline")
    graph.add_edge("timeline", "accountant")
    graph.add_edge("accountant", "reviewer")
    graph.add_edge("reviewer", END)
    return graph.compile()


_harness = build_harness()


def resolve_raw_data(raw_data: Optional[str], topic: Optional[str] = None) -> Dict[str, str]:
    text = (raw_data or "").strip()
    if text:
        return {"raw_data": text, "source": "user"}
    if topic and topic.strip():
        return {
            "raw_data": topic.strip(),
            "source": "system",
        }
    return {"raw_data": DEFAULT_RAW_DATA, "source": "system"}


async def run_pipeline(
    raw_data: Optional[str] = None,
    topic: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    resolved = resolve_raw_data(raw_data, topic)
    extracted, extract_source = await gather_source_material(
        raw_data=resolved["raw_data"] if resolved["source"] == "user" else (raw_data or ""),
        topic=topic,
        pdf_bytes=pdf_bytes,
    )
    if not extracted:
        extracted = resolved["raw_data"]
        extract_source = resolved["source"]

    source = "pdf" if extract_source == "pdf" else ("web" if extract_source == "web" else resolved["source"])
    initial: PipelineState = {
        "raw_data": resolved["raw_data"],
        "source": source,
        "extracted_content": extracted,
        "difficulty_score": 0,
        "structured": {},
        "timeline": {},
        "rewards": {},
        "compiled": {},
    }
    return await _harness.ainvoke(initial)


async def run_agent(user_message: str) -> Dict[str, Any]:
    return await run_pipeline(raw_data=user_message)
