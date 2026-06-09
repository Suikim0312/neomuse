"""Database initialization and seed data.

Creates all tables and inserts default users, exhibits, excursions and
tickets so the application is usable immediately after first launch.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import Base, SessionLocal, engine
from app.db.models import (
    Excursion,
    ExcursionBooking,
    ExcursionStatus,
    Exhibit,
    Ticket,
    TicketStatus,
    TicketType,
    User,
    UserRole,
)
from app.services.ticket_service import calculate_price, generate_qr_code

logger = logging.getLogger(__name__)


DEFAULT_USERS = [
    ("Администратор Системы", "admin@neomuse.local", "admin123", UserRole.admin),
    ("Менеджер Музея", "manager@neomuse.local", "manager123", UserRole.manager),
    ("Гид Экскурсовод", "guide@neomuse.local", "guide123", UserRole.guide),
    ("Посетитель Тестовый", "visitor@neomuse.local", "visitor123", UserRole.visitor),
]

DEFAULT_EXHIBITS = [
    {
        "title": "Золотой человек",
        "description": "Знаменитый сакский воин в золотом одеянии. Реконструкция погребального костюма воина из кургана Иссык.",
        "category": "Археология", "origin": "Казахстан", "period": "IV–III вв. до н.э.",
        "condition_status": "Отличное", "location_hall": "Зал 1",
        "image_url": "https://images.unsplash.com/photo-1599202860130-f600f4948364?w=600&q=80",
        "title_en": "Golden Man", "title_kz": "Алтын адам",
        "description_en": "Famous Saka warrior in golden attire. Reconstruction of the burial costume from the Issyk kurgan.",
        "description_kz": "Алтын киімдегі атақты сақ жауынгері. Есік қорғанынан табылған жерлеу костюмінің реконструкциясы.",
        "category_en": "Archaeology", "category_kz": "Археология",
        "period_en": "IV–III centuries BC", "period_kz": "б.з.д. IV–III ғғ.",
    },
    {
        "title": "Скифская пектораль",
        "description": "Нагрудное украшение из золота, найденное в кургане Товста Могила. Одно из крупнейших произведений скифского ювелирного искусства.",
        "category": "Ювелирное искусство", "origin": "Степь", "period": "IV в. до н.э.",
        "condition_status": "Хорошее", "location_hall": "Зал 1",
        "image_url": "https://images.unsplash.com/photo-1584208124888-3c0ac1e7f76a?w=600&q=80",
        "title_en": "Scythian Pectoral", "title_kz": "Скиф төс әшекейі",
        "description_en": "Golden pectoral ornament found in the Tovsta Mohyla kurgan. One of the largest Scythian gold pieces.",
        "description_kz": "Товста Могила қорғанынан табылған алтын төс әшекейі. Скиф алтынының ең ірі туындыларының бірі.",
        "category_en": "Jewelry Art", "category_kz": "Зергерлік өнер",
        "period_en": "IV century BC", "period_kz": "б.з.д. IV ғасыр",
    },
    {
        "title": "Древняя керамика",
        "description": "Коллекция расписных глиняных сосудов бронзового века Центральной Азии.",
        "category": "Археология", "origin": "Центральная Азия", "period": "II тыс. до н.э.",
        "condition_status": "Удовлетворительное", "location_hall": "Зал 2",
        "image_url": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=600&q=80",
        "title_en": "Ancient Ceramics", "title_kz": "Ежелгі қыш бұйымдары",
        "description_en": "Collection of painted clay vessels of the Bronze Age from Central Asia.",
        "description_kz": "Орталық Азияның қола дәуіріндегі боялған саз ыдыстар жинағы.",
        "category_en": "Archaeology", "category_kz": "Археология",
        "period_en": "II millennium BC", "period_kz": "б.з.д. II мыңжылдық",
    },
    {
        "title": "Кочевая юрта",
        "description": "Традиционное жилище казахских кочевников. Полная реконструкция с подлинными предметами быта XIX века.",
        "category": "Этнография", "origin": "Казахстан", "period": "XIX в.",
        "condition_status": "Отличное", "location_hall": "Зал 3",
        "image_url": "https://images.unsplash.com/photo-1520451644838-906a30f2a2f3?w=600&q=80",
        "title_en": "Nomadic Yurt", "title_kz": "Көшпелі киіз үй",
        "description_en": "Traditional dwelling of Kazakh nomads. Full reconstruction with authentic items of the 19th century.",
        "description_kz": "Қазақ көшпенділерінің дәстүрлі тұрғын үйі. XIX ғасырдың шынайы заттарымен толық реконструкция.",
        "category_en": "Ethnography", "category_kz": "Этнография",
        "period_en": "XIX century", "period_kz": "XIX ғасыр",
    },
    {
        "title": "Старинные монеты",
        "description": "Нумизматическая коллекция монет Шёлкового пути: дирхемы, динары и медные фелсы X–XIII веков.",
        "category": "Нумизматика", "origin": "Шёлковый путь", "period": "X–XIII вв.",
        "condition_status": "Хорошее", "location_hall": "Зал 2",
        "image_url": "https://images.unsplash.com/photo-1605792657660-596af9009e82?w=600&q=80",
        "title_en": "Ancient Coins", "title_kz": "Ежелгі тиындар",
        "description_en": "Numismatic collection of Silk Road coins: dirhams, dinars and copper fels of the X-XIII centuries.",
        "description_kz": "Жібек жолы тиындарының нумизматикалық коллекциясы: X-XIII ғасырлардың дирхемдері, динарлары және мыс фелстері.",
        "category_en": "Numismatics", "category_kz": "Нумизматика",
        "period_en": "X–XIII centuries", "period_kz": "X–XIII ғғ.",
    },
    {
        "title": "Наскальные рисунки Тамгалы",
        "description": "Высококачественные копии петроглифов урочища Тамгалы — памятника всемирного наследия ЮНЕСКО.",
        "category": "Искусство", "origin": "Казахстан", "period": "Бронзовый век",
        "condition_status": "Хорошее", "location_hall": "Зал 4",
        "image_url": "https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=600&q=80",
        "title_en": "Tamgaly Rock Paintings", "title_kz": "Тамғалы жартас суреттері",
        "description_en": "High-quality copies of petroglyphs from Tamgaly — a monument of world significance, UNESCO heritage.",
        "description_kz": "ЮНЕСКО мұрасы — Тамғалы ескерткішінің петроглифтерінің жоғары сапалы көшірмелері.",
        "category_en": "Art", "category_kz": "Өнер",
        "period_en": "Bronze Age", "period_kz": "Қола дәуірі",
    },
]


def _seed_users(db: Session) -> dict[UserRole, User]:
    users: dict[UserRole, User] = {}
    for full_name, email, password, role in DEFAULT_USERS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                full_name=full_name,
                email=email,
                hashed_password=hash_password(password),
                role=role,
            )
            db.add(user)
        users[role] = user
    db.commit()
    for user in users.values():
        db.refresh(user)
    return users


def _seed_exhibits(db: Session) -> None:
    if db.query(Exhibit).count() > 0:
        return
    for data in DEFAULT_EXHIBITS:
        db.add(Exhibit(**data))
    db.commit()


def _seed_excursions(db: Session, guide: User) -> None:
    if db.query(Excursion).count() > 0:
        return
    now = datetime.now(timezone.utc)
    samples = [
        {
            "title": "Обзорная экскурсия по музею",
            "description": "Знакомство с главными экспонатами.",
            "title_en": "Museum Overview Tour", "title_kz": "Мұражайды шолу экскурсиясы",
            "description_en": "Introduction to the main exhibits.",
            "description_kz": "Негізгі экспонаттармен танысу.",
            "start": now + timedelta(days=1, hours=2), "cap": 15,
        },
        {
            "title": "Тайны древних кочевников",
            "description": "Экскурсия по этнографическому залу.",
            "title_en": "Secrets of Ancient Nomads", "title_kz": "Ежелгі көшпенділердің сыры",
            "description_en": "Tour of the ethnographic hall.",
            "description_kz": "Этнографиялық зал бойынша экскурсия.",
            "start": now + timedelta(days=3, hours=4), "cap": 10,
        },
        {
            "title": "Сокровища Шёлкового пути",
            "description": "Нумизматика и торговые маршруты.",
            "title_en": "Treasures of the Silk Road", "title_kz": "Жібек жолының қазынасы",
            "description_en": "Numismatics and trade routes.",
            "description_kz": "Нумизматика және сауда жолдары.",
            "start": now + timedelta(days=5, hours=1), "cap": 12,
        },
    ]
    for s in samples:
        start = s.pop("start")
        cap = s.pop("cap")
        db.add(
            Excursion(
                guide_id=guide.id,
                start_time=start, end_time=start + timedelta(hours=1),
                max_participants=cap, status=ExcursionStatus.scheduled,
                **s,
            )
        )
    db.commit()


def _seed_tickets(db: Session, visitor: User) -> None:
    if db.query(Ticket).count() > 0:
        return
    now = datetime.now(timezone.utc)
    samples = [
        (TicketType.adult, TicketStatus.paid, now + timedelta(days=2)),
        (TicketType.student, TicketStatus.booked, now + timedelta(days=4)),
        (TicketType.child, TicketStatus.used, now - timedelta(days=1)),
    ]
    for ttype, status, visit_date in samples:
        db.add(
            Ticket(
                visitor_id=visitor.id, ticket_type=ttype, visit_date=visit_date,
                price=calculate_price(ttype), status=status,
                qr_code=generate_qr_code(ttype),
            )
        )
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = _seed_users(db)
        _seed_exhibits(db)
        _seed_excursions(db, users[UserRole.guide])
        _seed_tickets(db, users[UserRole.visitor])
        # one sample excursion booking
        if db.query(ExcursionBooking).count() == 0:
            excursion = db.query(Excursion).first()
            if excursion:
                db.add(
                    ExcursionBooking(
                        excursion_id=excursion.id,
                        visitor_id=users[UserRole.visitor].id,
                    )
                )
                db.commit()
        logger.info("Database initialized with seed data.")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
