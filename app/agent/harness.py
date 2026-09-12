from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.core import call_structured
from app.agent.schemas import CompiledTimeline, RewardsPlan, StructuredContent, TimelinePlan

DEFAULT_RAW_DATA = (
    "I want to ship a small personal project but I keep stalling. "
    "The idea is fuzzy, coding sessions are messy, I skip testing, "
    "and I never share the work. Turn this into a path I can actually follow."
)


class PipelineState(TypedDict):
    raw_data: str
    source: str
    structured: Dict[str, Any]
    timeline: Dict[str, Any]
    rewards: Dict[str, Any]
    compiled: Dict[str, Any]


async def structure_node(state: PipelineState) -> Dict[str, Any]:
    structured = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You classify and structure messy user material into a clean learning/task brief. "
                    "Keep the user's intent. Do not invent a different topic."
                ),
            },
            {
                "role": "user",
                "content": state["raw_data"],
            },
        ],
        StructuredContent,
    )
    return {"structured": structured.model_dump()}


async def timeline_node(state: PipelineState) -> Dict[str, Any]:
    timeline = await call_structured(
        [
            {
                "role": "system",
                "content": (
                    "You turn structured content into a gamified timeline of levels. "
                    "Create 3 to 5 levels that increase in difficulty. "
                    "Each level should list concrete things the user must do. "
                    "Difficulty must be easy, medium, or hard."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Build levels from this structured brief:\n"
                    f"{state['structured']}"
                ),
            },
        ],
        TimelinePlan,
    )
    return {"timeline": timeline.model_dump()}


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
                    "Fix missing points, mismatched task names, and unfair rewards. "
                    "Approve only if the path is coherent from start to finish."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Structured:\n{state['structured']}\n\n"
                    f"Timeline:\n{state['timeline']}\n\n"
                    f"Rewards:\n{state['rewards']}"
                ),
            },
        ],
        CompiledTimeline,
    )
    return {"compiled": compiled.model_dump()}


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
            "raw_data": (
                "The user did not provide source material. "
                f"Arrange a complete gamified path about: {topic.strip()}"
            ),
            "source": "system",
        }
    return {"raw_data": DEFAULT_RAW_DATA, "source": "system"}


async def run_pipeline(raw_data: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    resolved = resolve_raw_data(raw_data, topic)
    initial: PipelineState = {
        "raw_data": resolved["raw_data"],
        "source": resolved["source"],
        "structured": {},
        "timeline": {},
        "rewards": {},
        "compiled": {},
    }
    return await _harness.ainvoke(initial)


async def run_agent(user_message: str) -> Dict[str, Any]:
    return await run_pipeline(raw_data=user_message)
