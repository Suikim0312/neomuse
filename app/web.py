"""Server-rendered HTML pages (Jinja2) for the Russian-language UI.

These routes query the database directly and render templates. Auth is
cookie-based; the access_token cookie is set on login and cleared on
logout (logout is handled client-side by deleting the cookie).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.db.models import (
    BookingStatus,
    Excursion,
    ExcursionBooking,
    Exhibit,
    Ticket,
    User,
    UserRole,
)
from app.services.analytics_service import get_dashboard_stats
import random
import string

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def get_lang(request: Request) -> str:
    return request.cookies.get("lang", "ru")


def tfield(obj, field: str, lang: str) -> str:
    if lang != "ru":
        val = getattr(obj, f"{field}_{lang}", None)
        if val:
            return val
    return getattr(obj, field, "") or ""


templates.env.globals["tfield"] = tfield


def _render(name: str, ctx: dict, **kwargs):
    """Render a template using the current Starlette signature.

    The request is taken from the context dict that ``_ctx`` builds.
    """
    return templates.TemplateResponse(ctx["request"], name, ctx, **kwargs)

_ROLE_LABELS = {
    "ru": {"admin": "Администратор", "manager": "Менеджер", "guide": "Гид-Экскурсовод", "visitor": "Посетитель"},
    "en": {"admin": "Administrator", "manager": "Manager", "guide": "Tour Guide", "visitor": "Visitor"},
    "kz": {"admin": "Әкімші", "manager": "Менеджер", "guide": "Экскурсия гиді", "visitor": "Келуші"},
}
_TICKET_TYPE_LABELS = {
    "ru": {"adult": "Взрослый", "student": "Студенческий", "child": "Детский", "group": "Групповой"},
    "en": {"adult": "Adult", "student": "Student", "child": "Child", "group": "Group"},
    "kz": {"adult": "Ересек", "student": "Студент", "child": "Балалар", "group": "Топтық"},
}
_TICKET_STATUS_LABELS = {
    "ru": {"booked": "Забронирован", "paid": "Оплачен", "cancelled": "Отменён", "used": "Использован"},
    "en": {"booked": "Booked", "paid": "Paid", "cancelled": "Cancelled", "used": "Used"},
    "kz": {"booked": "Брондалған", "paid": "Төленген", "cancelled": "Болдырылмаған", "used": "Пайдаланылған"},
}
_EXCURSION_STATUS_LABELS = {
    "ru": {"scheduled": "Запланирована", "in_progress": "Идёт", "completed": "Завершена", "cancelled": "Отменена"},
    "en": {"scheduled": "Scheduled", "in_progress": "In Progress", "completed": "Completed", "cancelled": "Cancelled"},
    "kz": {"scheduled": "Жоспарланған", "in_progress": "Өтіп жатыр", "completed": "Аяқталған", "cancelled": "Болдырылмаған"},
}

def ROLE_LABELS(lang="ru"): return _ROLE_LABELS.get(lang, _ROLE_LABELS["ru"])
def TICKET_TYPE_LABELS(lang="ru"): return _TICKET_TYPE_LABELS.get(lang, _TICKET_TYPE_LABELS["ru"])
def TICKET_STATUS_LABELS(lang="ru"): return _TICKET_STATUS_LABELS.get(lang, _TICKET_STATUS_LABELS["ru"])
def EXCURSION_STATUS_LABELS(lang="ru"): return _EXCURSION_STATUS_LABELS.get(lang, _EXCURSION_STATUS_LABELS["ru"])


def _ctx(request: Request, user, **extra) -> dict:
    lang = get_lang(request)
    base = {
        "request": request,
        "user": user,
        "role_labels": ROLE_LABELS(lang),
        "ticket_type_labels": TICKET_TYPE_LABELS(lang),
        "ticket_status_labels": TICKET_STATUS_LABELS(lang),
        "excursion_status_labels": EXCURSION_STATUS_LABELS(lang),
        "now": datetime.now(timezone.utc),
        "lang": lang,
    }
    base.update(extra)
    return base


# ---------- Auth pages ----------
@router.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/exhibits", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user=Depends(get_current_user_optional)):
    return _render("auth/login.html", _ctx(request, user))


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user or not verify_password(password, db_user.hashed_password):
        return _render(
            "auth/login.html",
            _ctx(request, None, error="Неверный email или пароль"),
            status_code=401,
        )
    token = create_access_token(db_user.id, db_user.role.value)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        "access_token", f"Bearer {token}", httponly=True, samesite="lax"
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user=Depends(get_current_user_optional)):
    return _render("auth/register.html", _ctx(request, user))


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == email).first():
        return _render(
            "auth/register.html",
            _ctx(request, None, error="Пользователь с таким email уже существует"),
            status_code=400,
        )
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.visitor,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role.value)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        "access_token", f"Bearer {token}", httponly=True, samesite="lax"
    )
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return _render("auth/forgot_password.html", _ctx(request, None))


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        return _render(
            "auth/forgot_password.html",
            _ctx(request, None, error="Пользователь с таким email не найден"),
        )
    new_password = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    db_user.hashed_password = hash_password(new_password)
    db.commit()
    # Try to send via Telegram
    try:
        import os, httpx
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if bot_token and chat_id:
            msg = f"🔑 NeoMuse — сброс пароля\n\nEmail: {email}\nНовый пароль: {new_password}\n\nВойдите и смените пароль в настройках."
            httpx.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": msg},
                timeout=5,
            )
    except Exception:
        pass
    return _render(
        "auth/forgot_password.html",
        _ctx(request, None, success=True, new_password=new_password),
    )


@router.get("/exhibits/{exhibit_id}/detail")
def exhibit_detail_api(
    exhibit_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    from fastapi.responses import JSONResponse
    exhibit = db.get(Exhibit, exhibit_id)
    if not exhibit:
        return JSONResponse({"error": "not found"}, status_code=404)
    lang = get_lang(request)
    return JSONResponse({
        "id": exhibit.id,
        "title": tfield(exhibit, "title", lang),
        "description": tfield(exhibit, "description", lang),
        "category": tfield(exhibit, "category", lang),
        "period": tfield(exhibit, "period", lang),
        "origin": exhibit.origin,
        "condition_status": exhibit.condition_status,
        "location_hall": exhibit.location_hall,
        "is_available": exhibit.is_available,
        "image_url": exhibit.image_url or "",
    })


def _require_login(user, roles=None):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if roles and user.role not in roles:
        return RedirectResponse(url="/dashboard", status_code=303)
    return None


# ---------- Dashboard ----------
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect

    stats = None
    if user.role in (UserRole.admin, UserRole.manager):
        stats = get_dashboard_stats(db)
    return _render(
        "dashboard/index.html", _ctx(request, user, stats=stats)
    )


# ---------- Exhibits ----------
@router.get("/exhibits", response_class=HTMLResponse)
def exhibits_page(
    request: Request,
    search: str | None = None,
    category: str | None = None,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    query = db.query(Exhibit)
    if search:
        query = query.filter(Exhibit.title.ilike(f"%{search}%"))
    if category:
        query = query.filter(Exhibit.category == category)
    exhibits = query.order_by(Exhibit.created_at.desc()).all()
    categories = [c[0] for c in db.query(Exhibit.category).distinct().all() if c[0]]
    return _render(
        "exhibits/list.html",
        _ctx(request, user, exhibits=exhibits, categories=categories,
             search=search or "", selected_category=category or ""),
    )


@router.get("/exhibits/{exhibit_id}", response_class=HTMLResponse)
def exhibit_detail(
    exhibit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    exhibit = db.get(Exhibit, exhibit_id)
    if not exhibit:
        return RedirectResponse(url="/exhibits", status_code=303)
    return _render("exhibits/detail.html", _ctx(request, user, exhibit=exhibit))


@router.get("/exhibits/new", response_class=HTMLResponse)
def exhibit_new(
    request: Request, user=Depends(get_current_user_optional)
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    return _render(
        "exhibits/form.html", _ctx(request, user, exhibit=None)
    )


@router.post("/exhibits/new")
def exhibit_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    origin: str = Form(""),
    period: str = Form(""),
    condition_status: str = Form(""),
    location_hall: str = Form(""),
    image_url: str = Form(""),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    exhibit = Exhibit(
        title=title, description=description, category=category, origin=origin,
        period=period, condition_status=condition_status,
        location_hall=location_hall, image_url=image_url,
    )
    db.add(exhibit)
    db.commit()
    from app.services.cache_service import invalidate_exhibits
    invalidate_exhibits()
    return RedirectResponse(url="/exhibits", status_code=303)


@router.get("/exhibits/{exhibit_id}/edit", response_class=HTMLResponse)
def exhibit_edit(
    request: Request,
    exhibit_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    exhibit = db.get(Exhibit, exhibit_id)
    return _render(
        "exhibits/form.html", _ctx(request, user, exhibit=exhibit)
    )


@router.post("/exhibits/{exhibit_id}/edit")
def exhibit_update(
    request: Request,
    exhibit_id: int,
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    origin: str = Form(""),
    period: str = Form(""),
    condition_status: str = Form(""),
    location_hall: str = Form(""),
    image_url: str = Form(""),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit:
        exhibit.title = title
        exhibit.description = description
        exhibit.category = category
        exhibit.origin = origin
        exhibit.period = period
        exhibit.condition_status = condition_status
        exhibit.location_hall = location_hall
        exhibit.image_url = image_url
        db.commit()
        from app.services.cache_service import invalidate_exhibits
        invalidate_exhibits()
    return RedirectResponse(url="/exhibits", status_code=303)


@router.post("/exhibits/{exhibit_id}/delete")
def exhibit_delete(
    exhibit_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    exhibit = db.get(Exhibit, exhibit_id)
    if exhibit:
        db.delete(exhibit)
        db.commit()
        from app.services.cache_service import invalidate_exhibits
        invalidate_exhibits()
    return RedirectResponse(url="/exhibits", status_code=303)


# ---------- Tickets ----------
@router.get("/tickets", response_class=HTMLResponse)
def tickets_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    if user.role in (UserRole.admin, UserRole.manager):
        tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.visitor_id == user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )
    return _render(
        "tickets/list.html", _ctx(request, user, tickets=tickets)
    )


@router.get("/tickets/book", response_class=HTMLResponse)
def ticket_book_page(
    request: Request, user=Depends(get_current_user_optional)
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return _render("tickets/book.html", _ctx(request, user))


@router.post("/tickets/book")
def ticket_book_submit(
    request: Request,
    ticket_type: str = Form(...),
    visit_date: str = Form(...),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    from app.db.models import TicketStatus, TicketType
    from app.services.ticket_service import calculate_price, generate_qr_code

    ttype = TicketType(ticket_type)
    visit_dt = datetime.fromisoformat(visit_date)
    ticket = Ticket(
        visitor_id=user.id, ticket_type=ttype, visit_date=visit_dt,
        price=calculate_price(ttype), status=TicketStatus.booked,
        qr_code=generate_qr_code(ttype),
    )
    db.add(ticket)
    db.commit()
    from app.services.cache_service import invalidate_dashboard
    from app.services.telegram_service import send_notification
    invalidate_dashboard()
    send_notification(
        f"🎟 Забронирован билет ({ttype.value}) на {visit_dt:%d.%m.%Y}"
    )
    return RedirectResponse(url="/tickets", status_code=303)


# ---------- Excursions ----------
@router.get("/excursions", response_class=HTMLResponse)
def excursions_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    if user.role == UserRole.guide:
        excursions = (
            db.query(Excursion)
            .filter(Excursion.guide_id == user.id)
            .order_by(Excursion.start_time.asc())
            .all()
        )
    else:
        excursions = db.query(Excursion).order_by(Excursion.start_time.asc()).all()

    # participant counts
    counts = dict(
        db.query(ExcursionBooking.excursion_id, func.count(ExcursionBooking.id))
        .filter(ExcursionBooking.booking_status == BookingStatus.registered)
        .group_by(ExcursionBooking.excursion_id)
        .all()
    )
    guides = db.query(User).filter(User.role == UserRole.guide).all()
    user_bookings = set(
        row[0] for row in db.query(ExcursionBooking.excursion_id)
        .filter(
            ExcursionBooking.visitor_id == user.id,
            ExcursionBooking.booking_status == BookingStatus.registered,
        )
        .all()
    ) if user.role == UserRole.visitor else set()
    return _render(
        "excursions/list.html",
        _ctx(request, user, excursions=excursions, counts=counts, guides=guides, user_bookings=user_bookings),
    )


@router.post("/excursions/new")
def excursion_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    guide_id: str = Form(""),
    start_time: str = Form(...),
    end_time: str = Form(...),
    max_participants: int = Form(10),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    excursion = Excursion(
        title=title, description=description,
        guide_id=int(guide_id) if guide_id else None,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        max_participants=max_participants,
    )
    db.add(excursion)
    db.commit()
    from app.services.cache_service import invalidate_dashboard
    from app.services.telegram_service import send_notification
    invalidate_dashboard()
    send_notification(f"🗓 Создана экскурсия «{title}»")
    return RedirectResponse(url="/excursions", status_code=303)


@router.post("/excursions/{excursion_id}/status")
def excursion_status(
    excursion_id: int,
    status: str = Form(...),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager, UserRole.guide))
    if redirect:
        return redirect
    from app.db.models import ExcursionStatus

    excursion = db.get(Excursion, excursion_id)
    if excursion:
        if user.role == UserRole.guide and excursion.guide_id != user.id:
            return RedirectResponse(url="/excursions", status_code=303)
        excursion.status = ExcursionStatus(status)
        db.commit()
    return RedirectResponse(url="/excursions", status_code=303)


@router.post("/excursions/{excursion_id}/register")
def excursion_register(
    excursion_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    excursion = db.get(Excursion, excursion_id)
    if excursion:
        existing = (
            db.query(ExcursionBooking)
            .filter(
                ExcursionBooking.excursion_id == excursion_id,
                ExcursionBooking.visitor_id == user.id,
                ExcursionBooking.booking_status == BookingStatus.registered,
            )
            .first()
        )
        count = (
            db.query(func.count(ExcursionBooking.id))
            .filter(
                ExcursionBooking.excursion_id == excursion_id,
                ExcursionBooking.booking_status == BookingStatus.registered,
            )
            .scalar()
            or 0
        )
        if not existing and count < excursion.max_participants:
            db.add(
                ExcursionBooking(excursion_id=excursion_id, visitor_id=user.id)
            )
            db.commit()
    return RedirectResponse(url="/excursions", status_code=303)


@router.post("/excursions/{excursion_id}/unregister")
def excursion_unregister(
    excursion_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    booking = (
        db.query(ExcursionBooking)
        .filter(
            ExcursionBooking.excursion_id == excursion_id,
            ExcursionBooking.visitor_id == user.id,
            ExcursionBooking.booking_status == BookingStatus.registered,
        )
        .first()
    )
    if booking:
        db.delete(booking)
        db.commit()
    return RedirectResponse(url="/excursions", status_code=303)


# ---------- Reports ----------
@router.get("/reports", response_class=HTMLResponse)
def reports_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    import os

    from app.core.config import settings
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(settings.REPORTS_DIR) if f.endswith(".csv")],
        reverse=True,
    )
    return _render(
        "reports/index.html", _ctx(request, user, files=files)
    )


@router.post("/reports/generate")
def reports_generate(
    report_type: str = Form(...),
    user=Depends(get_current_user_optional),
):
    redirect = _require_login(user, (UserRole.admin, UserRole.manager))
    if redirect:
        return redirect
    from app.services.report_service import generate_report, generate_report_task
    try:
        generate_report_task.delay(report_type)
    except Exception:
        generate_report(report_type)
    return RedirectResponse(url="/reports", status_code=303)


# ---------- Users ----------
@router.get("/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin,))
    if redirect:
        return redirect
    users = db.query(User).order_by(User.created_at.desc()).all()
    return _render(
        "users/list.html", _ctx(request, user, users=users)
    )


@router.post("/users/{user_id}/toggle")
def user_toggle(
    user_id: int,
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user, (UserRole.admin,))
    if redirect:
        return redirect
    target = db.get(User, user_id)
    if target and target.id != user.id:
        target.is_active = not target.is_active
        db.commit()
    return RedirectResponse(url="/users", status_code=303)


# ---------- Profile ----------
@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request, user=Depends(get_current_user_optional)
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return _render("dashboard/profile.html", _ctx(request, user))


# ---------- Settings ----------
@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    user=Depends(get_current_user_optional),
    success: str | None = None,
    error: str | None = None,
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    return _render("dashboard/settings.html", _ctx(request, user, success=success, error=error))


@router.post("/settings/account")
def settings_account(
    request: Request,
    full_name: str = Form(""),
    email: str = Form(""),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    db_user = db.query(User).filter(User.id == user.id).first()
    if full_name.strip():
        db_user.full_name = full_name.strip()
    if email.strip():
        db_user.email = email.strip()
    db.commit()
    return RedirectResponse(url="/settings?success=Данные+обновлены", status_code=303)


@router.post("/settings/password")
def settings_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    redirect = _require_login(user)
    if redirect:
        return redirect
    if new_password != confirm_password:
        return RedirectResponse(url="/settings?error=Пароли+не+совпадают", status_code=303)
    db_user = db.query(User).filter(User.id == user.id).first()
    if not verify_password(current_password, db_user.hashed_password):
        return RedirectResponse(url="/settings?error=Неверный+текущий+пароль", status_code=303)
    db_user.hashed_password = hash_password(new_password)
    db.commit()
    return RedirectResponse(url="/settings?success=Пароль+изменён", status_code=303)
