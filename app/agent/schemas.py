from typing import List

from pydantic import BaseModel, Field


class StructuredContent(BaseModel):
    title: str
    category: str
    summary: str
    audience: str
    goals: List[str]
    key_topics: List[str]


class LevelTask(BaseModel):
    title: str
    description: str
    difficulty: str = Field(description="easy, medium, or hard")


class Level(BaseModel):
    level_number: int
    name: str
    difficulty: str
    objective: str
    tasks: List[LevelTask]


class TimelinePlan(BaseModel):
    title: str
    levels: List[Level]


class TaskReward(BaseModel):
    task_title: str
    points: int
    reward: str


class LevelReward(BaseModel):
    level_number: int
    level_points: int
    level_reward: str
    tasks: List[TaskReward]


class RewardsPlan(BaseModel):
    total_points: int
    levels: List[LevelReward]


class CompiledTask(BaseModel):
    title: str
    description: str
    difficulty: str
    points: int
    reward: str


class CompiledLevel(BaseModel):
    level_number: int
    name: str
    difficulty: str
    objective: str
    level_points: int
    level_reward: str
    tasks: List[CompiledTask]


class CompiledTimeline(BaseModel):
    title: str
    category: str
    summary: str
    total_points: int
    approved: bool
    review_notes: str
    levels: List[CompiledLevel]
