from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from app.utils.security import verify_password_reset_token
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional
from fastapi import  Depends, Request, status,FastAPI
from fastapi.responses import HTMLResponse
from app.models import  UserRole
from app.schemas import UserRead
from app.utils import get_current_user,delete_access_token_cookie,get_current_teacher_user
from app.models import User
from app.routers import (
    reading_texts,reading_assistant,
    akil_yurut, boslugu_doldur,
    hecelere_ayir, get_current_user_id,
    anlam_sec, harf_karistirma, kod_kirici,
    anlam_bagdastir,harf_karistirma_bosluk,
    nesne_yonu_tanima,ilk_harfi_yakala,
    yon_takibi,kelime_ses_uyum,auth,
    user_data_report,take_all_data,security_user,
    teacher_dashboard,flashcard,ai)
from app.config import settings
import os


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="LetStep - Okumada Yeni Bir Adım"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATIC_DIR = os.path.join(BASE_DIR, "static")

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(auth.router)
app.include_router(reading_texts.router)
app.include_router(reading_assistant.router)
app.include_router(akil_yurut.router)
app.include_router(boslugu_doldur.router)
app.include_router(hecelere_ayir.router)
app.include_router(get_current_user_id.router)
app.include_router(anlam_sec.router)
app.include_router(harf_karistirma.router)
app.include_router(kod_kirici.router)
app.include_router(anlam_bagdastir.router)
app.include_router(harf_karistirma_bosluk.router)
app.include_router(nesne_yonu_tanima.router)
app.include_router(ilk_harfi_yakala.router)
app.include_router(yon_takibi.router)
app.include_router(kelime_ses_uyum.router)
app.include_router(user_data_report.router)
app.include_router(take_all_data.router)
app.include_router(security_user.router)
app.include_router(teacher_dashboard.router)
app.include_router(flashcard.router)
app.include_router(ai.router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    if exc.status_code == 403:
        return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

    # Diğer HTTP hataları için varsayılan JSON yanıtını koruyabilirsiniz
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Bu handler'ı ise beklenmedik 500 hataları için kullanın
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Bu loglama çok önemli, hatanın ne olduğunu konsolda görebilirsiniz
    print(f"Beklenmedik bir sunucu hatası oluştu (500): {exc}")
    import traceback
    traceback.print_exc()

    return templates.TemplateResponse(
        "500.html", {"request": request}, status_code=500
    )

@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_index_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return templates.TemplateResponse("login.html", {"request": request})

    if current_user.role == UserRole.teacher:

        return templates.TemplateResponse(
            "index-html-with-teacher.html",
            {"request": request, "current_user": current_user}
        )
    else:
        return templates.TemplateResponse(
            "index-html-with-login.html",
            {"request": request, "current_user": current_user}
        )

def get_access_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("access_token")

@app.get("/admin-dashboard", response_class=HTMLResponse, tags=["Öğretmen Paneli"])
async def get_admin_dashboard_page(request: Request, teacher: User = Depends(get_current_teacher_user)):
    return templates.TemplateResponse("index-html-with-teacher.html", {"request": request})


@app.get("/admin-students", response_class=HTMLResponse, tags=["Öğretmen Paneli"])
async def get_admin_students_page(request: Request, teacher: User = Depends(get_current_teacher_user)):
    return templates.TemplateResponse("admin_students.html", {"request": request})


@app.get("/admin-reports", response_class=HTMLResponse, tags=["Öğretmen Paneli"])
async def get_admin_reports_page(
    request: Request,
    teacher: User = Depends(get_current_teacher_user),
    access_token: str | None = Depends(get_access_token_from_cookie)
):

    return templates.TemplateResponse(
        "admin_reports.html",
        {
            "request": request,
            "access_token": access_token
        }
    )


@app.get("/login", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_login_page(request: Request, current_user: Optional[User] = Depends(get_current_user)):
    if current_user:
        if current_user.role == "teacher":
            return RedirectResponse(url="/admin-dashboard", status_code=status.HTTP_303_SEE_OTHER)
        else:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    response = templates.TemplateResponse("login.html", {"request": request})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/register", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_register_page(current_user: Optional[User] = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    response = FileResponse(os.path.join(TEMPLATES_DIR, "register.html"), status_code=status.HTTP_200_OK)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/register-teacher", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_register_page(current_user: Optional[User] = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    response = FileResponse(os.path.join(TEMPLATES_DIR, "teacher-register.html"), status_code=status.HTTP_200_OK)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/forgot-password", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_login_page(current_user: Optional[User] = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    response = FileResponse(os.path.join(TEMPLATES_DIR, "forgot_password.html"), status_code=status.HTTP_200_OK)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/reset-password", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_reset_password_page(
        request: Request,
        current_user: Optional[User] = Depends(get_current_user)):

    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    token = request.query_params.get("token")

    email_from_token = verify_password_reset_token(token)

    if not email_from_token:
        return RedirectResponse(url="/login?error=invalid_token", status_code=status.HTTP_303_SEE_OTHER)

    response = FileResponse(os.path.join(TEMPLATES_DIR, "reset-password.html"), status_code=status.HTTP_200_OK)

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

@app.get("/dashboard", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_dashboard_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "dashboard.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/okuma_asistani", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_okuma_asistani_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "okuma-asistani.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/exercises", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_exercises_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "exercises.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/akil-yurut", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_anlam_sec_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "akil_yurut.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/boslugu-doldur", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_boslugu_doldur_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "boslugu-doldur.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/hecelere-ayir", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_hecelere_ayir_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "hecelere-ayir.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/anlam-sec", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "anlam-sec.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/harf-karistirma", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "harf-karistirma.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/kod-kirici", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "kod-kirici.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/anlam-bagdastir", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "anlam-bagdastir.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/harf-karistirma-bosluk", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "harf-karistirma-bosluk.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/nesne-yonu-tanima", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "nesne-yonu-tanima.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ilk-harfi-yakala", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "ilk-harfi-yakala.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response



@app.get("/yon-takibi", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "yon-takibi.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/kelime-ses-uyum", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "kelime-ses-uyum.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/user-rapor", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "user-rapor.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/security-settings", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "security_settings.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/flashcard", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "flashcard.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/ai", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "ai.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/ai-recommendation", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "ai_recommendation.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/ai-weekly", response_class=HTMLResponse, tags=["Sayfalar"])
async def get_renk_siralama_page(current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = os.path.join(TEMPLATES_DIR, "ai_weekly.html")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=302)
    delete_access_token_cookie(response)
    return response