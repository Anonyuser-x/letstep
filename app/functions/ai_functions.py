from datetime import datetime, timedelta, date
import json
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import google.generativeai as genai
from sqlalchemy import and_
# Modelleri import ediyoruz
from app.models import Exercise, UserActivity, WeeklyPlan, User, PlanTask,DailyTask
from app.config import settings

# API Anahtarını ve modeli yapılandırıyoruz
GEMINI_API_KEY = settings.GOOGLE_API_KEY
genai.configure(api_key=GEMINI_API_KEY)
AI_MODEL_NAME = 'gemini-2.5-pro'  # Çalışan modeli merkezi bir değişkene alıyoruz


async def generate_weekly_plan_service(user: User, db: AsyncSession):
    """
    Kullanıcının aktivitelerine göre yeni bir haftalık plan oluşturur ve yapısal olarak veritabanına kaydeder.
    """
    activity_result = await db.execute(select(UserActivity).filter(UserActivity.user_id == user.id))
    user_activities = activity_result.scalars().all()

    if not user_activities:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Plan oluşturmak için yeterli aktivite bulunmuyor.")

    exercise_result = await db.execute(select(Exercise))
    all_exercises = ", ".join([f"{e.game_type} ({e.category})" for e in exercise_result.scalars().all()])

    # Prompt, sadece ve sadece JSON döndürmesi için güncellendi.
    prompt = f"""
    Bir öğrenci için haftalık çalışma programı oluştur. Öğrencinin geçmiş aktiviteleri şunlardır:
    {[{'game_type': act.game_type, 'is_resolved': act.is_resolved, 'wrong_type': act.wrong_type} for act in user_activities]}

    Bu aktivitelere göre zayıf olduğu alanları belirle ve bu alanları güçlendirmeye yönelik bir plan oluştur.
    Plan hem fiziksel aktiviteler hem de şu dijital egzersizlerden oluşmalıdır: {all_exercises}.

    TÜM YANITIN SADECE VE SADECE AŞAĞIDAKİ YAPIDA GEÇERLİ BİR JSON NESNESİ OLMALIDIR.
    BAŞKA HİÇBİR AÇIKLAMA, METİN VEYA MARKDOWN (```) EKLEME.

    {{
        "subject": "Haftalık Gelişim Planı",
        "goal": "Bu hafta belirlenen zayıf alanları güçlendirme ve düzenli çalışma alışkanlığı kazanma.",
        "plan": [
            {{"day": "Pazartesi", "activity": "Sabah 15 dakika esneme hareketi", "duration_minutes": 15}},
            {{"day": "Pazartesi", "activity": "hecelere ayırma egzersizi", "duration_minutes": 20}},
            {{"day": "Salı", "activity": "anlam seçme egzersizi", "duration_minutes": 25}}
        ]
    }}
    """
    try:
        model = genai.GenerativeModel(AI_MODEL_NAME)
        # AI'ın JSON formatında cevap vermesini zorunlu kıl
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        plan_data = json.loads(response.text)

        new_weekly_plan = WeeklyPlan(
            user_id=user.id,
            subject=plan_data.get("subject", "Haftalık Plan"),
            goal=plan_data.get("goal", "Yapay zeka tarafından oluşturuldu.")
        )
        db.add(new_weekly_plan)
        await db.flush()

        tasks_to_create = [
            PlanTask(
                plan_id=new_weekly_plan.id,
                day_of_week=task_item.get("day"),
                activity=task_item.get("activity"),
                duration_minutes=task_item.get("duration_minutes")
            )
            for task_item in plan_data.get("plan", [])
        ]
        db.add_all(tasks_to_create)

        await db.commit()
        await db.refresh(new_weekly_plan, ["tasks"])
        return new_weekly_plan

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Plan oluşturulurken bir hata oluştu: {str(e)}")


async def get_or_create_daily_tasks_service(user: User, db: AsyncSession):
    """
    Kullanıcı için günlük görevleri kontrol eder. Eğer o gün için görev oluşturulmamışsa,
    yapay zeka kullanarak 4 yeni görev oluşturur, veritabanına kaydeder ve döndürür.
    Eğer görevler zaten varsa, mevcut görevleri döndürür.
    """
    today = date.today()

    # Bugün oluşturulmuş görev var mı diye kontrol et
    query = select(DailyTask).filter(
        DailyTask.user_id == user.id,
        and_(
            DailyTask.created_at >= today,
            DailyTask.created_at < today + timedelta(days=1)
        )
    ).order_by(DailyTask.id)

    result = await db.execute(query)
    existing_tasks = result.scalars().all()

    if existing_tasks:
        return existing_tasks  # Eğer görevler varsa, direkt onları döndür

    # Eğer görev yoksa yeni görevler oluştur
    activity_result = await db.execute(select(UserActivity).filter(UserActivity.user_id == user.id).limit(20))
    user_activities = activity_result.scalars().all()

    if not user_activities:
        # Aktivite yoksa genel başlangıç görevleri oluştur
        tasks_list = [
            "Bugün hedeflerini gözden geçir.",
            "10 dakika yürüyüş yap.",
            "Bir 'anlam seçme' egzersizi tamamla.",
            "Kendine sağlıklı bir atıştırmalık hazırla."
        ]
    else:
        # Aktivite varsa, yapay zekadan görev iste
        prompt = f"""
        Öğrencinin son aktivitelerine göre, onun eksiklerini kapatacak, öğrenme motivasyonunu artıracak ve gelişimini destekleyecek 4 adet kısa, eyleme geçirilebilir ve motive edici günlük görev oluştur.

        Aktivite verileri: {[{'game_type': act.game_type, 'is_resolved': act.is_resolved, 'wrong_type': act.wrong_type} for act in user_activities]}

        Görevler:
        - Öğrencinin hatalı yaptığı alanlara odaklanmalı.
        - Tekrara düşmeden çeşitlilik içermeli.
        - Basit, açık ve aksiyon odaklı ifadeler kullanılmalı.
        - Görevler öğrencinin motivasyonunu artıracak şekilde pozitif bir dille yazılmalı.
        - Gerekiyorsa önceki yanlışlardan ders çıkarılmasını teşvik etmeli.
        - Gereksiz soyutlama veya genel ifadelerden kaçınılmalı.

        TÜM YANITIN SADECE VE SADECE AŞAĞIDAKİ YAPIDA BİR JSON NESNESİ OLMALIDIR.
        BAŞKA HİÇBİR AÇIKLAMA VEYA MARKDOWN (```) EKLEME.

        
        "tasks": [
                "Görev 1 açıklaması",
                "Görev 2 açıklaması",
                "Görev 3 açıklaması",
                "Görev 4 açıklaması"
            ]
        
        """
        try:
            model = genai.GenerativeModel(AI_MODEL_NAME)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            tasks_data = json.loads(response.text)
            tasks_list = tasks_data.get("tasks", [])
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Yapay zeka ile görev oluşturulurken bir hata oluştu: {str(e)}")

    # Yeni görevleri veritabanına kaydet
    new_tasks = [DailyTask(user_id=user.id, description=desc) for desc in tasks_list]
    db.add_all(new_tasks)
    await db.commit()

    # Kaydedilen görevleri geri döndür
    for task in new_tasks:
        await db.refresh(task)

    return new_tasks