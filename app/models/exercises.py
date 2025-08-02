from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    game_type = Column(String, nullable=False)
    category = Column(String, nullable=False)


    user_exercises = relationship("UserExercise", back_populates="exercise", cascade="all, delete-orphan")
    akil_yurut_questions = relationship("AkilYurutQuestion", back_populates="exercise", cascade="all, delete-orphan")
    boslugu_doldur_questions = relationship("BosluguDoldurQuestion", back_populates="exercise", cascade="all, delete-orphan")
    hecelere_ayir_questions = relationship("HecelereAyirQuestion", back_populates="exercise", cascade="all, delete-orphan")
    anlam_sec_questions = relationship("AnlamSecQuestion", back_populates="exercise", cascade="all, delete-orphan")
    harf_karistirma_questions = relationship("HarfKaristirmaQuestion", back_populates="exercise", cascade="all, delete-orphan")
    kod_kirici_questions = relationship("KodKiriciQuestion", back_populates="exercise", cascade="all, delete-orphan")
    anlam_bagdastir_questions = relationship("AnlamBagdastirQuestion", back_populates="exercise", cascade="all, delete-orphan")
    harf_karistirma_bosluk_questions = relationship("HarfKaristirmaBoslukQuestion", back_populates="exercise", cascade="all, delete-orphan")
    nesne_yonu_tanima_questions = relationship("NesneYonuTanimaQuestion", back_populates="exercise", cascade="all, delete-orphan")
    ilk_harfi_yakala_questions= relationship("IlkHarfiYakalaQuestion", back_populates="exercise", cascade="all, delete-orphan")
    yon_takibi_questions= relationship("YonTakibiQuestion", back_populates="exercise", cascade="all, delete-orphan")
    kelime_ses_uyum_questions= relationship("KelimeSesUyumQuestion", back_populates="exercise", cascade="all, delete-orphan")


