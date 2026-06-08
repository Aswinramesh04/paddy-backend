"""
Database initializer.
  - Creates all tables (idempotent).
  - Seeds disease catalogue if the table is empty.
Run once at startup via lifespan or manually: python -m app.db.init_db
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal, engine
from app.models import disease, recommendation, shop, prediction  # registers metadata

log = get_logger(__name__)

# ── Seed data ─────────────────────────────────────────────────
DISEASE_SEED = [
    {
        "class_index": 0,
        "name": "Blast Disease",
        "name_ta": "நெல் கருகல் நோய்",
        "name_hi": "ब्लास्ट रोग",
        "description": "Blast is a fungal disease caused by Magnaporthe oryzae that affects paddy leaves, nodes, and grains.",
        "symptoms": "Diamond-shaped lesions with gray centers and brown borders on leaves. Neck rot at panicle base.",
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Tricyclazole 75% WP",
                "dosage": "Mix 0.6g in 1 litre of water and spray uniformly",
                "how_to_use": "Spray on affected leaves during early morning or late evening.",
                "benefits": "Controls blast fungus effectively. Protects leaves and grains. Improves yield.",
                "precautions": "Use gloves while spraying. Do not spray in strong sunlight.",
                "medicine_type": "fungicide",
                "price_range": "₹80-120 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Bavistin 50% WP",
                "dosage": "1g per litre of water",
                "how_to_use": "Spray thoroughly on leaves and stem.",
                "benefits": "Broad-spectrum fungicide. Prevents secondary infections.",
                "precautions": "Avoid contact with eyes. Wash hands after use.",
                "medicine_type": "fungicide",
                "price_range": "₹60-90 per 100g",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Use resistant varieties",
            "Avoid excess nitrogen",
            "Maintain proper field hygiene",
            "Remove infected plant debris after harvest",
        ],
    },
    {
        "class_index": 1,
        "name": "Brown Spot",
        "name_ta": "பழுப்பு புள்ளி நோய்",
        "name_hi": "भूरा धब्बा",
        "description": "Brown spot is caused by Cochliobolus miyabeanus. It mainly affects leaves and grains.",
        "symptoms": "Oval to circular brown spots on leaves with yellow halo. Dark brown specks on grains.",
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Mancozeb 75% WP",
                "dosage": "2g per litre of water",
                "how_to_use": "Spray 2-3 times at 10-day intervals.",
                "benefits": "Broad protection against fungal diseases. Cost-effective.",
                "precautions": "Wear mask while spraying. Avoid spraying near water bodies.",
                "medicine_type": "fungicide",
                "price_range": "₹40-60 per 100g",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Use balanced fertilizers — avoid potassium deficiency",
            "Treat seeds with thiram before planting",
            "Maintain optimal plant spacing",
        ],
    },
    {
        "class_index": 2,
        "name": "Bacterial Leaf Blight",
        "name_ta": "பாக்டீரியா இலை கருகல்",
        "name_hi": "बैक्टीरियल लीफ ब्लाइट",
        "description": "Caused by Xanthomonas oryzae, bacterial leaf blight is one of the most serious diseases in rice.",
        "symptoms": "Water-soaked, yellowish stripes along leaf margins that turn straw-colored and wilt.",
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Copper Oxychloride 50% WP",
                "dosage": "3g per litre of water",
                "how_to_use": "Spray on both sides of leaves. Repeat after 7 days.",
                "benefits": "Effective bactericide. Prevents spread to healthy plants.",
                "precautions": "Do not mix with alkaline pesticides.",
                "medicine_type": "bactericide",
                "price_range": "₹50-80 per 100g",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Use resistant varieties",
            "Avoid flood irrigation during outbreak",
            "Remove infected plants promptly",
            "Disinfect farm equipment",
        ],
    },
    {
        "class_index": 3,
        "name": "Leaf Smut",
        "name_ta": "இலை கரிவெளி நோய்",
        "name_hi": "पत्ती कालिमा",
        "description": "Leaf smut is caused by Entyloma oryzae. It produces black powdery masses on leaf surfaces.",
        "symptoms": "Small, angular black spots scattered on leaves, appearing like soot.",
        "severity": "low",
        "recommendations": [
            {
                "medicine_name": "Propiconazole 25% EC",
                "dosage": "1ml per litre of water",
                "how_to_use": "Spray evenly on leaf surfaces.",
                "benefits": "Systemic fungicide, absorbed well by plants.",
                "precautions": "Avoid overdose. Keep away from children.",
                "medicine_type": "fungicide",
                "price_range": "₹90-130 per 100ml",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Crop rotation helps reduce pathogen load",
            "Use certified disease-free seeds",
        ],
    },
    {
        "class_index": 4,
        "name": "Sheath Blight",
        "name_ta": "கவச அழுகல் நோய்",
        "name_hi": "शीथ ब्लाइट",
        "description": "Sheath blight is caused by Rhizoctonia solani. It is common in high-yielding varieties.",
        "symptoms": "Oval or irregular lesions on leaf sheaths near water level. Lesions have white centers with brown borders.",
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Hexaconazole 5% EC",
                "dosage": "2ml per litre of water",
                "how_to_use": "Direct spray towards base of plant at waterline.",
                "benefits": "Controls sheath blight effectively. Systemic action.",
                "precautions": "Use protective gear. Avoid run-off into water.",
                "medicine_type": "fungicide",
                "price_range": "₹70-100 per 100ml",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Avoid excessive nitrogen application",
            "Maintain optimum plant density",
            "Drain water periodically",
        ],
    },
    {
        "class_index": 5,
        "name": "False Smut",
        "name_ta": "பொய் கரிவெளி நோய்",
        "name_hi": "झूठा काला कण",
        "description": "False smut is caused by Ustilaginoidea virens. It converts rice grains into velvety balls.",
        "symptoms": "Orange/green velvety balls replacing individual grains in panicle.",
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Propiconazole 25% EC",
                "dosage": "1ml per litre",
                "how_to_use": "Spray at booting stage for best results.",
                "benefits": "Prevents spore development in panicle.",
                "precautions": "Time application correctly at booting stage.",
                "medicine_type": "fungicide",
                "price_range": "₹90-130 per 100ml",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Use disease-free seeds",
            "Spray fungicide at boot leaf and heading stage",
            "Avoid late planting",
        ],
    },
    {
        "class_index": 6,
        "name": "Tungro",
        "name_ta": "டுங்க்ரோ நோய்",
        "name_hi": "टुंग्रो वायरस",
        "description": "Tungro is a viral disease transmitted by green leafhoppers. It is caused by two viruses working together.",
        "symptoms": "Yellow to orange leaf discoloration. Stunted growth. Reduced tillering.",
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Carbofuran 3G",
                "dosage": "1kg per 100 sq meters",
                "how_to_use": "Apply as granules in standing water near roots.",
                "benefits": "Controls leafhopper vector. Systemic insecticide.",
                "precautions": "Highly toxic — use gloves and mask. Keep away from fish ponds.",
                "medicine_type": "insecticide",
                "price_range": "₹120-160 per kg",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Use resistant varieties",
            "Control leafhopper population with insecticides",
            "Avoid continuous rice cropping",
            "Remove volunteer rice plants",
        ],
    },
    {
        "class_index": 7,
        "name": "Narrow Brown Leaf Spot",
        "name_ta": "குறுகிய பழுப்பு இலை புள்ளி",
        "name_hi": "संकरा भूरा धब्बा",
        "description": "Caused by Cercospora janseana. It produces narrow, linear brown lesions on rice leaves.",
        "symptoms": "Narrow, linear brown lesions running along the leaf veins.",
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Carbendazim 50% WP",
                "dosage": "1g per litre of water",
                "how_to_use": "Spray at first sign of disease and repeat in 14 days.",
                "benefits": "Systemic protection. Moves upward in plant.",
                "precautions": "Do not apply near harvest. Follow PHI guidelines.",
                "medicine_type": "fungicide",
                "price_range": "₹55-85 per 100g",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Use silicon-based fertilizers to strengthen leaf tissue",
            "Practice balanced fertilization",
        ],
    },
    {
        "class_index": 8,
        "name": "Rice Hispa",
        "name_ta": "நெல் இலை தின்னும் வண்டு",
        "name_hi": "राइस हिस्पा",
        "description": "Rice hispa (Dicladispa armigera) is an insect pest. Adults and larvae damage leaves.",
        "symptoms": "White parallel streaks on leaves caused by larvae tunneling. Adults scrape leaf surface leaving white patches.",
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Chlorpyrifos 20% EC",
                "dosage": "2ml per litre of water",
                "how_to_use": "Spray on leaves, especially upper surface where adults feed.",
                "benefits": "Kills adults and prevents further egg laying.",
                "precautions": "Do not spray during flowering. Keep out of reach of children.",
                "medicine_type": "insecticide",
                "price_range": "₹60-90 per 100ml",
                "order_index": 0,
            },
        ],
        "prevention_tips": [
            "Clip and destroy affected tillers",
            "Avoid high nitrogen application which attracts hispa",
            "Use light traps to monitor adult population",
        ],
    },
    {
        "class_index": 9,
        "name": "Healthy",
        "name_ta": "ஆரோக்கியமான நெல்",
        "name_hi": "स्वस्थ पौधा",
        "description": "The paddy plant appears healthy with no visible signs of disease or pest damage.",
        "symptoms": "Lush green leaves with uniform color. No spots, lesions, or discoloration.",
        "severity": "low",
        "recommendations": [],
        "prevention_tips": [
            "Continue regular crop monitoring",
            "Maintain balanced fertilization schedule",
            "Ensure proper irrigation management",
            "Practice crop rotation in next season",
        ],
    },
]

SHOP_SEED = [
    {
        "name": "Sri Agri Store",
        "address": "12, Main Road, Tiruppur, Tamil Nadu - 641601",
        "phone": "+914212345678",
        "latitude": 11.1085,
        "longitude": 77.3411,
        "rating": 4.5,
        "review_count": 128,
        "opening_time": "08:00",
        "closing_time": "20:00",
        "is_open": True,
        "available_medicines": json.dumps(["Tricyclazole 75% WP", "Bavistin 50% WP", "Mancozeb 75% WP"]),
        "city": "Tiruppur",
        "state": "Tamil Nadu",
    },
    {
        "name": "Green Care Agro",
        "address": "45, Station Road, Coimbatore, Tamil Nadu - 641001",
        "phone": "+914222345679",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "rating": 4.3,
        "review_count": 89,
        "opening_time": "09:00",
        "closing_time": "19:00",
        "is_open": True,
        "available_medicines": json.dumps(["Carbofuran 3G", "Hexaconazole 5% EC", "Propiconazole 25% EC"]),
        "city": "Coimbatore",
        "state": "Tamil Nadu",
    },
    {
        "name": "Farmers World",
        "address": "78, Bypass Road, Erode, Tamil Nadu - 638001",
        "phone": "+914242345680",
        "latitude": 11.3410,
        "longitude": 77.7172,
        "rating": 4.2,
        "review_count": 64,
        "opening_time": "08:30",
        "closing_time": "20:30",
        "is_open": True,
        "available_medicines": json.dumps(["Chlorpyrifos 20% EC", "Copper Oxychloride 50% WP", "Carbendazim 50% WP"]),
        "city": "Erode",
        "state": "Tamil Nadu",
    },
]


def create_tables() -> None:
    """Create all database tables."""
    from app.db.database import Base
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created.")


def seed_diseases(db: Session) -> None:
    if db.query(Disease).count() > 0:
        log.info("Disease table already seeded — skipping.")
        return

    for item in DISEASE_SEED:
        recs = item.pop("recommendations", [])
        tips = item.pop("prevention_tips", [])

        disease = Disease(**item)
        db.add(disease)
        db.flush()  # get disease.id

        for i, rec in enumerate(recs):
            rec["order_index"] = i
            db.add(Recommendation(disease_id=disease.id, **rec))

        for i, tip in enumerate(tips):
            db.add(PreventionTip(disease_id=disease.id, tip=tip, order_index=i))

    db.commit()
    log.info(f"Seeded {len(DISEASE_SEED)} diseases.")


def seed_shops(db: Session) -> None:
    if db.query(Shop).count() > 0:
        log.info("Shop table already seeded — skipping.")
        return

    for item in SHOP_SEED:
        db.add(Shop(**item))
    db.commit()
    log.info(f"Seeded {len(SHOP_SEED)} shops.")


def init_db() -> None:
    create_tables()
    db = SessionLocal()
    try:
        seed_diseases(db)
        seed_shops(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")