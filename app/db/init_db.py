"""
Database initializer.
  - Creates all tables (idempotent — safe to run multiple times).
  - Seeds disease catalogue with all 10 real classes if table is empty.

Run manually:
    python -m app.db.init_db

Called automatically at startup via app/main.py lifespan.

10 Classes (alphabetical = model output order):
  0  bacterial_leaf_blight
  1  bacterial_leaf_streak
  2  bacterial_panicle_blight
  3  blast
  4  brown_spot
  5  dead_heart
  6  downy_mildew
  7  hispa
  8  normal
  9  tungro
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import Base, SessionLocal, engine

log = get_logger(__name__)

# ── Import all models so Base.metadata knows about them ───────
from app.models.user import User          # noqa: F401
from app.models.otp import OTP            # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.shop import Shop          # noqa: F401
from app.models.disease import Disease, Recommendation, PreventionTip  # noqa: F401


# ── Seed Data — 10 real classes ───────────────────────────────
DISEASE_SEED = [
    # ── 0: bacterial_leaf_blight ──────────────────────────────
    {
        "class_index": 0,
        "name": "Bacterial Leaf Blight",
        "name_ta": "பாக்டீரியா இலை கருகல்",
        "name_hi": "बैक्टीरियल लीफ ब्लाइट",
        "name_te": "బాక్టీరియల్ లీఫ్ బ్లైట్",
        "description": (
            "Bacterial Leaf Blight (BLB) is caused by Xanthomonas oryzae pv. oryzae. "
            "It is one of the most destructive diseases of rice, especially in tropical "
            "and subtropical regions. It spreads through water, wind, and infected seeds."
        ),
        "symptoms": (
            "Water-soaked to yellowish stripes along leaf margins and tips. "
            "Lesions turn straw-yellow and wilt from the tip downward. "
            "In severe cases, entire leaves die. Milky or opaque dew drops "
            "visible on lesion edges in early morning (bacterial ooze)."
        ),
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Copper Oxychloride 50% WP",
                "dosage": "3g per litre of water",
                "how_to_use": "Spray on both sides of leaves. Repeat after 7–10 days.",
                "benefits": "Effective bactericide. Prevents spread to healthy plants. Protects vascular tissue.",
                "precautions": "Do not mix with alkaline pesticides. Wear gloves and mask. Avoid spraying in strong wind.",
                "medicine_type": "bactericide",
                "price_range": "₹50–80 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Streptomycin Sulphate 90% SP",
                "dosage": "0.5g per litre of water",
                "how_to_use": "Mix well and spray uniformly on affected plants. Use 2–3 times at weekly intervals.",
                "benefits": "Antibiotic action. Rapidly controls bacterial spread. Systemic protection.",
                "precautions": "Use strictly as directed. Overuse causes resistance. Do not apply near harvest.",
                "medicine_type": "bactericide",
                "price_range": "₹120–180 per 100g",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Use resistant varieties such as IR64, TN1",
            "Use certified disease-free seeds",
            "Avoid flood irrigation during disease outbreak",
            "Drain field water when disease is spotted",
            "Remove and destroy infected plant debris",
            "Disinfect farm tools and equipment",
        ],
    },

    # ── 1: bacterial_leaf_streak ─────────────────────────────
    {
        "class_index": 1,
        "name": "Bacterial Leaf Streak",
        "name_ta": "பாக்டீரியா இலை கோடு நோய்",
        "name_hi": "बैक्टीरियल लीफ स्ट्रीक",
        "name_te": "బాక్టీరియల్ లీఫ్ స్ట్రీక్",
        "description": (
            "Bacterial Leaf Streak (BLS) is caused by Xanthomonas oryzae pv. oryzicola. "
            "It is common in warm, humid conditions and spreads through rain splash and wind. "
            "Often confused with Bacterial Leaf Blight but has distinct narrow streaks."
        ),
        "symptoms": (
            "Narrow, water-soaked, interveinal streaks on leaves that turn yellowish-brown. "
            "Streaks are translucent when held against light. Yellow bacterial ooze dries "
            "into yellowish beads on streak surface. Lesions do not extend to leaf margins "
            "(unlike BLB)."
        ),
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Copper Hydroxide 77% WP",
                "dosage": "2.5g per litre of water",
                "how_to_use": "Spray thoroughly on leaves, especially the underside. Repeat every 10 days.",
                "benefits": "Broad-spectrum bactericide. Protective and curative action.",
                "precautions": "Avoid application during heavy rain. Use protective gear.",
                "medicine_type": "bactericide",
                "price_range": "₹80–120 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Streptomycin + Copper Oxychloride (Blitox + Strep mix)",
                "dosage": "2g Copper Oxychloride + 0.5g Streptomycin per litre",
                "how_to_use": "Combine and spray on affected areas at first sign of disease.",
                "benefits": "Dual-action treatment. Controls spread faster than single agent.",
                "precautions": "Do not exceed dosage. Wear full protective equipment.",
                "medicine_type": "bactericide",
                "price_range": "₹100–150 per treatment",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Avoid overhead irrigation which splashes bacteria between plants",
            "Maintain proper plant spacing for airflow",
            "Reduce nitrogen fertilizer — excess promotes bacterial growth",
            "Remove crop residues after harvest",
        ],
    },

    # ── 2: bacterial_panicle_blight ──────────────────────────
    {
        "class_index": 2,
        "name": "Bacterial Panicle Blight",
        "name_ta": "பாக்டீரியா கதிர் கருகல்",
        "name_hi": "बैक्टीरियल पैनिकल ब्लाइट",
        "name_te": "బాక్టీరియల్ పానికల్ బ్లైట్",
        "description": (
            "Bacterial Panicle Blight is caused by Burkholderia glumae. "
            "It primarily affects rice panicles during grain filling stage. "
            "Hot and humid weather at heading stage favors disease development. "
            "Can cause significant yield loss in affected fields."
        ),
        "symptoms": (
            "Grain discoloration — infected grains turn pale to grayish-brown or tan. "
            "Sterility of florets. Panicles may be partially or fully sterile. "
            "Rotting at the base of panicle in severe cases. "
            "Infected seeds are shriveled and lighter weight."
        ),
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Propiconazole 25% EC",
                "dosage": "1ml per litre of water",
                "how_to_use": "Spray at booting stage (before heading) and repeat at heading. Focus spray on panicle area.",
                "benefits": "Systemic protection of panicle. Reduces grain sterility.",
                "precautions": "Time application before disease establishment. Use during cool hours.",
                "medicine_type": "fungicide",
                "price_range": "₹90–130 per 100ml",
                "order_index": 0,
            },
            {
                "medicine_name": "Copper Oxychloride 50% WP",
                "dosage": "3g per litre of water",
                "how_to_use": "Spray at panicle emergence. Repeat in 7 days.",
                "benefits": "Protects florets from bacterial infection during critical stage.",
                "precautions": "Spray in early morning. Avoid spraying on open flowers.",
                "medicine_type": "bactericide",
                "price_range": "₹50–80 per 100g",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Use heat-tolerant and resistant varieties",
            "Avoid planting during peak heat periods",
            "Use disease-free certified seeds — seed treatment with Pseudomonas fluorescens",
            "Drain field 2 weeks before heading to reduce bacterial soil load",
            "Avoid late-season nitrogen application",
        ],
    },

    # ── 3: blast ─────────────────────────────────────────────
    {
        "class_index": 3,
        "name": "Blast",
        "name_ta": "நெல் கருகல் நோய்",
        "name_hi": "ब्लास्ट रोग",
        "name_te": "బ్లాస్ట్ వ్యాధి",
        "description": (
            "Rice Blast is caused by the fungus Magnaporthe oryzae. "
            "It is considered the most important fungal disease of rice worldwide. "
            "It can infect leaves (leaf blast), neck (neck blast), and nodes (node blast). "
            "Neck blast is the most damaging, causing complete loss of panicle."
        ),
        "symptoms": (
            "Leaf blast: Diamond or spindle-shaped lesions with gray-white center "
            "and brown to red-brown border on leaves. "
            "Neck blast: Dark brown or black lesion at base of panicle neck — "
            "panicle breaks and falls (neck rot). "
            "Node blast: Blackening and rotting of stem nodes."
        ),
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Tricyclazole 75% WP",
                "dosage": "0.6g per litre of water (600g per hectare)",
                "how_to_use": (
                    "Mix in water and spray uniformly on leaves. "
                    "First spray at tillering, second at panicle initiation. "
                    "Spray during early morning or late evening for best results."
                ),
                "benefits": (
                    "Specific and highly effective against blast fungus. "
                    "Systemic action — absorbed by plant tissue. "
                    "Protects leaves, nodes, and neck."
                ),
                "precautions": "Wear gloves and mask. Do not spray in strong sunlight. Observe 14-day pre-harvest interval.",
                "medicine_type": "fungicide",
                "price_range": "₹80–120 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Isoprothiolane 40% EC (Fuji-One)",
                "dosage": "1.5ml per litre of water",
                "how_to_use": "Spray 2 times — at active tillering and booting stage.",
                "benefits": "Systemic fungicide with curative and protective action. Also improves root growth.",
                "precautions": "Avoid contact with skin and eyes. Do not use near water bodies.",
                "medicine_type": "fungicide",
                "price_range": "₹100–150 per 100ml",
                "order_index": 1,
            },
            {
                "medicine_name": "Carbendazim 50% WP",
                "dosage": "1g per litre of water",
                "how_to_use": "Spray at first sign of disease. Repeat every 10–14 days.",
                "benefits": "Broad-spectrum systemic fungicide. Effective against multiple fungal diseases.",
                "precautions": "Follow PHI guidelines. Do not apply near harvest.",
                "medicine_type": "fungicide",
                "price_range": "₹55–85 per 100g",
                "order_index": 2,
            },
        ],
        "prevention_tips": [
            "Use blast-resistant varieties (IR64, Swarna, ADT36)",
            "Avoid excess nitrogen fertilizer — promotes susceptibility",
            "Maintain proper field hygiene — remove infected debris",
            "Avoid continuous flooding — let soil dry periodically",
            "Plant at recommended spacing to reduce humidity in canopy",
            "Use silicon fertilizers to strengthen leaf tissue against penetration",
        ],
    },

    # ── 4: brown_spot ─────────────────────────────────────────
    {
        "class_index": 4,
        "name": "Brown Spot",
        "name_ta": "பழுப்பு புள்ளி நோய்",
        "name_hi": "भूरा धब्बा रोग",
        "name_te": "బ్రౌన్ స్పాట్",
        "description": (
            "Brown Spot is caused by the fungus Cochliobolus miyabeanus (Helminthosporium oryzae). "
            "It is most severe on nutrient-deficient soils, especially potassium and silicon deficient. "
            "Also infects seeds, causing seed discoloration and poor germination."
        ),
        "symptoms": (
            "Circular to oval spots on leaves — brown to dark brown with yellow halo. "
            "Spots have light brown or gray center. "
            "On grains: dark brown spots causing discoloration (stackburn). "
            "Severe infection causes premature drying of leaves."
        ),
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Mancozeb 75% WP",
                "dosage": "2g per litre of water",
                "how_to_use": "Spray 2–3 times at 10–14 day intervals starting at first sign of disease.",
                "benefits": "Broad-spectrum protective fungicide. Cost-effective. Prevents spore germination.",
                "precautions": "Wear mask while spraying. Avoid spraying near water bodies or ponds.",
                "medicine_type": "fungicide",
                "price_range": "₹40–60 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Propiconazole 25% EC",
                "dosage": "1ml per litre of water",
                "how_to_use": "Spray systemically. Absorbed and moves within plant tissue.",
                "benefits": "Systemic curative action. Controls established infections.",
                "precautions": "Avoid overdose — can cause phytotoxicity. Follow label instructions.",
                "medicine_type": "fungicide",
                "price_range": "₹90–130 per 100ml",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Apply balanced fertilization — especially potassium and silicon",
            "Treat seeds with thiram or captan before planting",
            "Use certified disease-free seeds",
            "Maintain optimal plant spacing",
            "Avoid drought stress — maintain consistent moisture",
        ],
    },

    # ── 5: dead_heart ─────────────────────────────────────────
    {
        "class_index": 5,
        "name": "Dead Heart",
        "name_ta": "இதய வாடல் (தண்டு துளைப்பான்)",
        "name_hi": "डेड हार्ट (तना छेदक)",
        "name_te": "డెడ్ హార్ట్ (స్టెమ్ బోరర్)",
        "description": (
            "Dead Heart is caused by stem borer larvae (Scirpophaga incertulas — Yellow Stem Borer "
            "or Scirpophaga innotata — White Stem Borer). "
            "The larvae bore into the stem and feed on the central shoot, "
            "cutting off nutrient supply and causing the central shoot to die. "
            "It is a major insect pest problem, not a fungal disease."
        ),
        "symptoms": (
            "Vegetative stage: Central tiller turns yellow then brown and dries out — "
            "called Dead Heart. Dead tiller pulls out easily with a gentle tug. "
            "Reproductive stage: Panicle turns white and sterile — called White Ear. "
            "Small round holes visible on stem where larvae entered."
        ),
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Chlorpyrifos 20% EC",
                "dosage": "2ml per litre of water",
                "how_to_use": "Spray on stems and lower leaf area. Spray when egg masses are visible for best control.",
                "benefits": "Kills stem borer larvae and adults. Prevents re-infestation.",
                "precautions": "Highly toxic — use full protective gear. Do not spray during flowering. Keep away from fish ponds.",
                "medicine_type": "insecticide",
                "price_range": "₹60–90 per 100ml",
                "order_index": 0,
            },
            {
                "medicine_name": "Carbofuran 3G (Granules)",
                "dosage": "1kg per 100 sq meters, broadcast in standing water",
                "how_to_use": "Apply granules in 2–3 cm standing water. Best applied at early tillering stage.",
                "benefits": "Systemic insecticide absorbed through roots. Long residual action (3–4 weeks).",
                "precautions": "HIGHLY TOXIC — use rubber gloves. Never apply near fish ponds or drinking water sources.",
                "medicine_type": "insecticide",
                "price_range": "₹120–160 per kg",
                "order_index": 1,
            },
            {
                "medicine_name": "Cartap Hydrochloride 4G",
                "dosage": "18–20 kg per hectare as granules",
                "how_to_use": "Broadcast in flooded field. Do not drain water for 3 days after application.",
                "benefits": "Specific to stem borers. Lower mammalian toxicity than Carbofuran.",
                "precautions": "Do not allow livestock near treated field. Follow PHI (30 days).",
                "medicine_type": "insecticide",
                "price_range": "₹200–300 per kg",
                "order_index": 2,
            },
        ],
        "prevention_tips": [
            "Clip and destroy egg masses found on leaves",
            "Use light traps to monitor and reduce adult moth population",
            "Release Trichogramma japonicum egg parasitoids (biological control)",
            "Avoid ratoon crop which harbors borer population",
            "Cut stems at ground level after harvest to destroy pupae",
            "Avoid late transplanting which coincides with peak borer flight",
        ],
    },

    # ── 6: downy_mildew ───────────────────────────────────────
    {
        "class_index": 6,
        "name": "Downy Mildew",
        "name_ta": "இறங்கு பூஞ்சை நோய்",
        "name_hi": "डाउनी मिल्ड्यू",
        "name_te": "డౌనీ మిల్డ్యూ",
        "description": (
            "Downy Mildew of rice is caused by Sclerophthora macrospora (Crazy Top) "
            "or Peronosclerospora species. It is a soil and waterborne disease that "
            "infects young seedlings. Cool temperatures and waterlogged conditions favor spread."
        ),
        "symptoms": (
            "Pale green or yellow streaks on leaves. "
            "White downy growth on underside of infected leaves (fungal sporulation). "
            "Twisted, malformed, or rolled leaves. "
            "Severely infected plants are stunted with abnormal tillering. "
            "Panicles may be replaced by leaf-like structures (virescence)."
        ),
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Metalaxyl 35% WS (seed treatment)",
                "dosage": "6g per kg of seed",
                "how_to_use": "Mix with seed before sowing. Ensures systemic protection from germination.",
                "benefits": "Prevents systemic infection from the start. High efficacy against oomycetes.",
                "precautions": "Use recommended dose only. Keep treated seeds separate from food.",
                "medicine_type": "fungicide",
                "price_range": "₹150–200 per 100g",
                "order_index": 0,
            },
            {
                "medicine_name": "Mancozeb 75% WP",
                "dosage": "2g per litre of water",
                "how_to_use": "Spray on foliar parts at first sign. Repeat every 10 days.",
                "benefits": "Broad-spectrum protective coverage. Prevents secondary spread.",
                "precautions": "Wear mask. Avoid drift onto neighboring crops.",
                "medicine_type": "fungicide",
                "price_range": "₹40–60 per 100g",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Avoid waterlogging — improve field drainage",
            "Use certified healthy seeds",
            "Treat seeds with Metalaxyl before sowing",
            "Remove and destroy infected plants early",
            "Avoid planting in low-lying areas prone to flooding",
        ],
    },

    # ── 7: hispa ──────────────────────────────────────────────
    {
        "class_index": 7,
        "name": "Hispa",
        "name_ta": "நெல் இலை தின்னும் வண்டு",
        "name_hi": "राइस हिस्पा (पत्ती खाने वाला कीड़ा)",
        "name_te": "హిస్పా (ఆకు తినే పురుగు)",
        "description": (
            "Rice Hispa (Dicladispa armigera) is a beetle pest. "
            "Both adult beetles and larvae cause damage. "
            "Adults scrape the upper leaf surface. "
            "Larvae tunnel through leaf tissue between the upper and lower epidermis. "
            "Severe infestation can destroy entire leaf area."
        ),
        "symptoms": (
            "White, parallel streaks or blotches on leaves caused by larval tunneling (mining). "
            "Adult feeding causes irregular white scratch marks on upper leaf surface. "
            "In severe cases, entire leaves turn white and dry up. "
            "Look for tiny black beetles (3–4mm) on leaf surface."
        ),
        "severity": "moderate",
        "recommendations": [
            {
                "medicine_name": "Chlorpyrifos 20% EC",
                "dosage": "2ml per litre of water",
                "how_to_use": "Spray on upper surface of leaves focusing on growing shoots. Repeat after 10 days.",
                "benefits": "Kills adult hispa beetles quickly. Prevents further egg laying.",
                "precautions": "Do not spray during flowering. Avoid near water. Use protective gear.",
                "medicine_type": "insecticide",
                "price_range": "₹60–90 per 100ml",
                "order_index": 0,
            },
            {
                "medicine_name": "Imidacloprid 17.8% SL",
                "dosage": "0.5ml per litre of water",
                "how_to_use": "Spray at first sign of adult beetle appearance. One application usually sufficient.",
                "benefits": "Systemic insecticide. Long residual protection. Very effective against sucking/chewing pests.",
                "precautions": "Do not use near flowering plants or bee colonies. Highly toxic to beneficial insects.",
                "medicine_type": "insecticide",
                "price_range": "₹70–100 per 100ml",
                "order_index": 1,
            },
        ],
        "prevention_tips": [
            "Clip and destroy affected tillers showing white streaks",
            "Use light traps to monitor and reduce adult beetle population",
            "Avoid excessive nitrogen application which attracts hispa",
            "Keep field bunds clean and weed-free",
            "Introduce predatory beetles as biological control",
        ],
    },

    # ── 8: normal ─────────────────────────────────────────────
    {
        "class_index": 8,
        "name": "Normal (Healthy)",
        "name_ta": "ஆரோக்கியமான நெல்",
        "name_hi": "स्वस्थ पौधा",
        "name_te": "ఆరోగ్యకరమైన వరి",
        "description": (
            "The paddy plant appears healthy with no visible signs of disease, "
            "pest damage, or nutrient deficiency. "
            "Lush green, vigorous growth indicates proper crop health."
        ),
        "symptoms": (
            "Lush green leaves with uniform color. "
            "No spots, lesions, streaks, or discoloration. "
            "Normal tillering and growth pattern. "
            "No visible pests or egg masses."
        ),
        "severity": "low",
        "recommendations": [],
        "prevention_tips": [
            "Continue regular crop monitoring every 7 days",
            "Maintain balanced NPK fertilization schedule",
            "Ensure proper irrigation — avoid waterlogging and drought stress",
            "Practice integrated pest management (IPM)",
            "Keep field bunds clean to prevent pest entry",
            "Plan crop rotation for next season",
        ],
    },

    # ── 9: tungro ─────────────────────────────────────────────
    {
        "class_index": 9,
        "name": "Tungro",
        "name_ta": "டுங்க்ரோ வைரஸ் நோய்",
        "name_hi": "टुंग्रो वायरस रोग",
        "name_te": "టుంగ్రో వైరస్",
        "description": (
            "Tungro is caused by two viruses working together: "
            "Rice Tungro Bacilliform Virus (RTBV) and Rice Tungro Spherical Virus (RTSV). "
            "It is transmitted by the green leafhopper (Nephotettix virescens). "
            "Tungro is among the most economically damaging rice diseases in Asia."
        ),
        "symptoms": (
            "Bright yellow to orange-yellow leaf discoloration starting from leaf tip. "
            "Stunted plant growth and reduced tillering. "
            "Leaves may be partially rolled and mottled. "
            "Delayed flowering and poorly filled grains. "
            "Plants infected early may not produce any panicle."
        ),
        "severity": "high",
        "recommendations": [
            {
                "medicine_name": "Carbofuran 3G (Granules)",
                "dosage": "1kg per 100 sq meters",
                "how_to_use": "Apply as granules in 2–3cm standing water at transplanting. Targets leafhopper vector.",
                "benefits": "Controls leafhopper population which transmits tungro virus. Systemic and long-lasting.",
                "precautions": "HIGHLY TOXIC — wear rubber gloves and boots. Never apply near fish ponds or drinking water.",
                "medicine_type": "insecticide",
                "price_range": "₹120–160 per kg",
                "order_index": 0,
            },
            {
                "medicine_name": "Imidacloprid 17.8% SL",
                "dosage": "0.5ml per litre of water",
                "how_to_use": "Spray at first sign of leafhopper presence. Focus on base of plant.",
                "benefits": "Fast knockdown of leafhopper vectors. Prevents virus transmission.",
                "precautions": "Do not apply near flowering stage. Harmful to bees. Use protective gear.",
                "medicine_type": "insecticide",
                "price_range": "₹70–100 per 100ml",
                "order_index": 1,
            },
            {
                "medicine_name": "Buprofezin 25% SC",
                "dosage": "1ml per litre of water",
                "how_to_use": "Spray at nymph stage of leafhopper for best results.",
                "benefits": "Insect growth regulator — disrupts molting of leafhoppers. Low toxicity to mammals.",
                "precautions": "Most effective against nymphs not adults. Apply early in infestation.",
                "medicine_type": "insecticide",
                "price_range": "₹90–130 per 100ml",
                "order_index": 2,
            },
        ],
        "prevention_tips": [
            "Use tungro-resistant varieties (TN1, IR36, IR64)",
            "Avoid continuous rice cropping — practice crop rotation",
            "Remove volunteer rice plants which harbor leafhopper",
            "Synchronize planting in a region to break leafhopper cycle",
            "Install yellow sticky traps to monitor leafhopper population",
            "Maintain field water to discourage leafhopper movement",
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
        "available_medicines": json.dumps([
            "Tricyclazole 75% WP", "Carbofuran 3G",
            "Mancozeb 75% WP", "Copper Oxychloride 50% WP",
        ]),
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
        "available_medicines": json.dumps([
            "Chlorpyrifos 20% EC", "Imidacloprid 17.8% SL",
            "Propiconazole 25% EC", "Metalaxyl 35% WS",
        ]),
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
        "available_medicines": json.dumps([
            "Carbendazim 50% WP", "Streptomycin Sulphate 90% SP",
            "Buprofezin 25% SC", "Cartap Hydrochloride 4G",
        ]),
        "city": "Erode",
        "state": "Tamil Nadu",
    },
]


# ── Core functions ────────────────────────────────────────────

def create_tables() -> None:
    """Create all database tables. Safe to call multiple times (idempotent)."""
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created (or already exist).")


def seed_diseases(db: Session) -> None:
    """Seed disease catalogue. Skips if already populated."""
    if db.query(Disease).count() > 0:
        log.info("Disease table already seeded — skipping.")
        return

    log.info("Seeding disease catalogue ...")
    for item in DISEASE_SEED:
        recs_data = item.pop("recommendations", [])
        tips_data = item.pop("prevention_tips", [])

        disease = Disease(**item)
        db.add(disease)
        db.flush()  # Get disease.id before adding children

        for rec in recs_data:
            db.add(Recommendation(disease_id=disease.id, **rec))

        for idx, tip_text in enumerate(tips_data):
            db.add(PreventionTip(disease_id=disease.id, tip=tip_text, order_index=idx))

    db.commit()
    log.info(f"Seeded {len(DISEASE_SEED)} diseases with recommendations and tips.")


def seed_shops(db: Session) -> None:
    """Seed agro shop data. Skips if already populated."""
    if db.query(Shop).count() > 0:
        log.info("Shop table already seeded — skipping.")
        return

    log.info("Seeding shop data ...")
    for item in SHOP_SEED:
        db.add(Shop(**item))
    db.commit()
    log.info(f"Seeded {len(SHOP_SEED)} shops.")


def init_db() -> None:
    """
    Full DB initialization:
      1. Create all tables
      2. Seed diseases (10 classes)
      3. Seed shops
    Called automatically on app startup.
    """
    create_tables()
    db = SessionLocal()
    try:
        seed_diseases(db)
        seed_shops(db)
    except Exception as exc:
        log.error(f"Database seeding failed: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    """Run directly: python -m app.db.init_db"""
    from app.core.logging import setup_logging
    setup_logging()
    log.info("Running database initialization manually ...")
    init_db()
    log.info("Done. All tables created and seeded successfully.")