from typing import List

from pydantic import BaseModel, Field


class StructuredContent(BaseModel):
    title: str
    category: str
    summary: str
    audience: str
    goals: List[str]
    key_topics: List[str]
    difficulty_score: int = Field(ge=0, le=100, description="Overall difficulty from 0 (easiest) to 100 (hardest)")


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


class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(min_length=2, description="Multiple-choice options")
    correct_option_index: int = Field(ge=0, description="0-based index of the correct option")


class Checkpoint(BaseModel):
    checkpoint_number: int = Field(ge=1)
    title: str
    content: str = Field(description="Lesson content for this checkpoint, drawn from the source material")
    difficulty: str = Field(description="easy, medium, or hard; later checkpoints should be harder")
    objective: str
    questionnaire: List[QuizQuestion] = Field(
        min_length=10,
        max_length=10,
        description="Exactly 10 questions to check progress after this checkpoint",
    )


class TimelinePlan(BaseModel):
    title: str
    checkpoint_count: int
    checkpoints: List[Checkpoint]


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
    difficulty_score: int = Field(ge=0, le=100)
    approved: bool
    review_notes: str
    levels: List[CompiledLevel]
