from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from app.models import UserActivity, UserTrophy, User, UserExercise
from app.schemas import UserReport, OverallStats, RecentActivity, ChartData, UserJourneyReport, JourneyDay, Trophy


async def get_user_development_report(current_user: User, db: AsyncSession):
    stmt_stats = (
        select(
            func.sum(UserExercise.total_questions).label("total_questions_solved"),
            func.sum(UserExercise.correct_answer).label("total_correct_answers")
        )
        .filter(UserExercise.user_id == current_user.id)
    )
    result_stats = await db.execute(stmt_stats)
    user_stats = result_stats.first()

    stmt_logs = select(UserActivity).filter_by(user_id=current_user.id, is_resolved=0).order_by(
        UserActivity.datetime.desc())
    result_logs = await db.execute(stmt_logs)
    user_logs = result_logs.scalars().all()

    if not user_logs:
        return UserReport(
            overall_stats=OverallStats(total_questions_solved=0, most_challenging_category="Yok", avg_reaction_time=0,
                                       total_correct_answers=0),
            recent_activities=[], chart_data=ChartData(labels=[], data=[]),
            weekly_performance={}
        )

    total_questions_solved = user_stats.total_questions_solved if user_stats and user_stats.total_questions_solved else 0
    total_correct_answers = user_stats.total_correct_answers if user_stats and user_stats.total_correct_answers else 0
    total_reaction_time = sum(log.reaction_time for log in user_logs)
    avg_reaction_time = round(total_reaction_time / len(user_logs), 2) if user_logs else 0
    category_counts = defaultdict(int)
    for log in user_logs: category_counts[log.category.capitalize()] += 1
    most_challenging_category = max(category_counts, key=category_counts.get) if category_counts else "Yok"

    overall_stats_data = OverallStats(
        total_questions_solved=total_questions_solved,
        most_challenging_category=most_challenging_category,
        avg_reaction_time=avg_reaction_time,
        total_correct_answers=total_correct_answers
    )

    recent_activities_data = [RecentActivity.from_orm(log) for log in user_logs[:4]]

    game_type_counts = defaultdict(int)
    today = date.today()
    for log in user_logs:
        if log.datetime.date() > (today - timedelta(days=7)): game_type_counts[log.game_type] += 1
    sorted_game_types = sorted(game_type_counts.items(), key=lambda item: item[1], reverse=True)
    chart_data_obj = ChartData(labels=[item[0] for item in sorted_game_types],
                               data=[item[1] for item in sorted_game_types])

    day_of_week_counts = defaultdict(int)
    for log in user_logs:
        if log.day_of_week:
            day_of_week_counts[log.day_of_week.capitalize()] += 1

    ordered_days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    weekly_performance_data = {day: day_of_week_counts.get(day, 0) for day in ordered_days}

    return UserReport(
        overall_stats=overall_stats_data,
        recent_activities=recent_activities_data,
        chart_data=chart_data_obj,
        weekly_performance=weekly_performance_data
    )


async def get_user_journey_report(current_user: User, db: AsyncSession):
    stmt = select(UserActivity).filter_by(user_id=current_user.id, is_resolved=0).order_by(UserActivity.datetime.asc())
    result = await db.execute(stmt)
    user_logs = result.scalars().all()

    if not user_logs:
        return UserJourneyReport(journey_data=[], total_activities=0, avg_reaction_time_overall=0.0,
                                 most_frequent_category=None)


    daily_data = defaultdict(lambda: {'logs': []})
    for log in user_logs:
        daily_data[log.datetime.date()]['logs'].append(log)

    journey_data_list = []
    for log_date, data in sorted(daily_data.items()):
        day_logs = data['logs']
        avg_reaction_time = round(sum(l.reaction_time for l in day_logs) / len(day_logs), 2)
        categories = sorted(list(set(l.category.capitalize() for l in day_logs)))

        day_activities = [RecentActivity.from_orm(log) for log in day_logs]

        journey_data_list.append(
            JourneyDay(
                journey_date=log_date,
                reaction_time=avg_reaction_time,
                total_questions=len(day_logs),
                categories=categories,
                activities=day_activities
            )
        )

    total_activities = len(user_logs)
    avg_reaction_time_overall = round(sum(l.reaction_time for l in user_logs) / total_activities, 2)
    category_counts = defaultdict(int)
    for log in user_logs: category_counts[log.category.capitalize()] += 1
    most_frequent_category = max(category_counts, key=category_counts.get) if category_counts else None

    return UserJourneyReport(
        journey_data=journey_data_list, total_activities=total_activities,
        avg_reaction_time_overall=avg_reaction_time_overall, most_frequent_category=most_frequent_category
    )


async def get_and_update_trophies(current_user: User, report_data: UserJourneyReport, db: AsyncSession):
    # İleriye yönelik database kısmına madalya listeleri eklenecek
    ALL_TROPHIES = {
        "azim_madalyasi": Trophy(id="azim_madalyasi", title="Azim Madalyası", description="50'den fazla tekrar yaptın!",
                                 icon="fa-medal", color_class="gold"),
        "hiz_roketi": Trophy(id="hiz_roketi", title="Hız Roketi", description="Ortalama hızın 10 saniyenin altında!",
                             icon="fa-rocket", color_class="gold"),
        "maratoncu": Trophy(id="maratoncu", title="Maratoncu", description="15 farklı günde pratik yaptın!",
                            icon="fa-calendar-check", color_class="silver"),
        "haftalik_yildiz": Trophy(id="haftalik_yildiz", title="Haftalık Yıldız",
                                  description="Bu hafta 5 farklı günde çalıştın!", icon="fa-star",
                                  color_class="bronze"),
    }

    stmt = select(UserTrophy).filter_by(user_id=current_user.id)
    result = await db.execute(stmt)
    earned_trophies_db = result.scalars().all()
    earned_trophy_ids = {trophy.trophy_id for trophy in earned_trophies_db}

    newly_earned_trophies = []

    if report_data.total_activities > 50 and "azim_madalyasi" not in earned_trophy_ids:
        new_trophy = UserTrophy(user_id=current_user.id, trophy_id="azim_madalyasi")
        db.add(new_trophy)
        newly_earned_trophies.append(new_trophy)

    if report_data.avg_reaction_time_overall < 10 and "hiz_roketi" not in earned_trophy_ids:
        new_trophy = UserTrophy(user_id=current_user.id, trophy_id="hiz_roketi")
        db.add(new_trophy)
        newly_earned_trophies.append(new_trophy)

    if len(report_data.journey_data) > 15 and "maratoncu" not in earned_trophy_ids:
        new_trophy = UserTrophy(user_id=current_user.id, trophy_id="maratoncu")
        db.add(new_trophy)
        newly_earned_trophies.append(new_trophy)

    today = date.today()
    last_7_days_practice_days = {day.journey_date for day in report_data.journey_data if
                                 day.journey_date > (today - timedelta(days=7))}
    if len(last_7_days_practice_days) >= 5 and "haftalik_yildiz" not in earned_trophy_ids:
        new_trophy = UserTrophy(user_id=current_user.id, trophy_id="haftalik_yildiz")
        db.add(new_trophy)
        newly_earned_trophies.append(new_trophy)

    if newly_earned_trophies:
        await db.commit()
        for trophy in newly_earned_trophies:
            earned_trophy_ids.add(trophy.trophy_id)

    return [ALL_TROPHIES[trophy_id] for trophy_id in earned_trophy_ids]