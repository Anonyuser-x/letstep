from pydantic import BaseModel
from datetime import date, datetime
from typing import List,Dict

class OverallStats(BaseModel):
    total_questions_solved: int
    most_challenging_category: str
    avg_reaction_time: float
    total_correct_answers: int

class RecentActivity(BaseModel):
    game_type: str
    selected_answer: str
    correct_answer: str
    datetime: datetime

    class Config:
        from_attributes = True

class ChartData(BaseModel):
    labels: List[str]
    data: List[int]

class UserReport(BaseModel):
    overall_stats: OverallStats
    recent_activities: List[RecentActivity]
    chart_data: ChartData
    weekly_performance: Dict[str, int]

class JourneyDay(BaseModel):
    journey_date: date
    reaction_time: float
    total_questions: int
    categories: list[str]
    activities: list[RecentActivity]

    class Config:
        from_attributes = True

class UserJourneyReport(BaseModel):
    journey_data: List[JourneyDay]
    total_activities: int
    avg_reaction_time_overall: float
    most_frequent_category: str | None

class Trophy(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    color_class: str