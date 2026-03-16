"""
Script to populate the Gemach database with 100+ real medicines.
Run this script from your project root:
    python populate_medicines.py
"""

import os
import sys
import django
from datetime import date

# ── Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gemach.settings')
django.setup()

from bot.models import Medicine

# ── Medicine data
# Fields: name, name_hebrew, quantity, expiry_date, min_age, suitable_pregnant
MEDICINES = [
    # ── Pain relievers / Antipyretics
    ("Acamol",          "אקמול",          8,  date(2027, 6, 30),  0,  True),
    ("Acamol Forte",    "אקמול פורטה",    5,  date(2027, 3, 31),  12, False),
    ("Optalgin",        "אופטלגין",       6,  date(2026, 12, 31), 6,  False),
    ("Advil",           "אדוויל",         4,  date(2027, 1, 31),  6,  False),
    ("Nurofen",         "נורופן",         7,  date(2027, 4, 30),  6,  False),
    ("Nurofen Junior",  "נורופן ג'וניור", 5,  date(2026, 11, 30), 0,  False),
    ("Dexamol",         "דקסמול",         3,  date(2027, 2, 28),  0,  True),
    ("Paracetamol",     "פרצטמול",        10, date(2027, 8, 31),  0,  True),
    ("Dipyrone",        "דיפירון",        4,  date(2026, 10, 31), 3,  False),
    ("Aspirin",         "אספירין",        6,  date(2027, 5, 31),  12, False),

    # ── Antibiotics
    ("Amoxicillin",     "אמוקסיצילין",   3,  date(2027, 1, 31),  0,  True),
    ("Augmentin",       "אוגמנטין",       2,  date(2026, 9, 30),  0,  True),
    ("Azithromycin",    "אזיתרומיצין",   4,  date(2027, 3, 31),  6,  False),
    ("Penicillin",      "פניצילין",       2,  date(2026, 8, 31),  0,  True),
    ("Cefalexin",       "צפלקסין",        3,  date(2027, 2, 28),  0,  True),
    ("Doxycycline",     "דוקסיציקלין",   2,  date(2027, 4, 30),  8,  False),
    ("Trimethoprim",    "טרימתופרים",     1,  date(2026, 7, 31),  0,  False),
    ("Ciprofloxacin",   "ציפרופלוקסצין", 2,  date(2027, 6, 30),  18, False),
    ("Erythromycin",    "אריתרומיצין",   1,  date(2026, 11, 30), 0,  True),
    ("Metronidazole",   "מטרונידזול",    2,  date(2027, 1, 31),  0,  False),

    # ── Respiratory
    ("Ventolin",        "ונטולין",        5,  date(2027, 7, 31),  2,  True),
    ("Flixotide",       "פליקסוטיד",     3,  date(2027, 2, 28),  4,  True),
    ("Seretide",        "סרטייד",         2,  date(2026, 12, 31), 4,  False),
    ("Atrovent",        "אטרובנט",        2,  date(2027, 3, 31),  6,  False),
    ("Bricanyl",        "בריקניל",        3,  date(2027, 1, 31),  6,  True),
    ("Berodual",        "ברודואל",        2,  date(2026, 10, 31), 6,  False),
    ("Pulmicort",       "פולמיקורט",     2,  date(2027, 5, 31),  6,  True),
    ("Symbicort",       "סימביקורט",     1,  date(2027, 4, 30),  12, False),
    ("Spiriva",         "ספיריבה",        1,  date(2027, 6, 30),  18, False),
    ("Montelukast",     "מונטלוקסט",     3,  date(2027, 2, 28),  2,  True),

    # ── Allergy
    ("Claritin",        "קלריטין",        8,  date(2027, 8, 31),  2,  False),
    ("Zyrtec",          "זירטק",          6,  date(2027, 3, 31),  2,  False),
    ("Aerius",          "אריוס",          5,  date(2027, 1, 31),  1,  False),
    ("Telfast",         "טלפסט",          4,  date(2026, 12, 31), 6,  False),
    ("Fenistil",        "פניסטיל",        3,  date(2027, 4, 30),  1,  False),
    ("Benadryl",        "בנדריל",         4,  date(2027, 2, 28),  2,  False),
    ("Phenergan",       "פנרגן",          2,  date(2026, 11, 30), 2,  False),
    ("Polaramine",      "פולרמין",        3,  date(2027, 5, 31),  2,  False),

    # ── Digestive
    ("Omeprazole",      "אומפרזול",       7,  date(2027, 6, 30),  0,  False),
    ("Losec",           "לוסק",           5,  date(2027, 3, 31),  0,  False),
    ("Nexium",          "נקסיום",         4,  date(2027, 1, 31),  0,  False),
    ("Zantac",          "זנטק",           3,  date(2026, 9, 30),  0,  False),
    ("Gaviscon",        "גביסקון",        6,  date(2027, 4, 30),  0,  True),
    ("Maalox",          "מאלוקס",         5,  date(2027, 2, 28),  0,  True),
    ("Imodium",         "אימודיום",       4,  date(2027, 7, 31),  6,  False),
    ("Dulcolax",        "דולקולקס",       3,  date(2027, 5, 31),  6,  False),
    ("Bisacodyl",       "ביסקודיל",       4,  date(2027, 3, 31),  6,  False),
    ("Normacol",        "נורמקול",        3,  date(2027, 1, 31),  0,  True),
    ("Domperidone",     "דומפרידון",      3,  date(2026, 12, 31), 0,  False),
    ("Metoclopramide",  "מטוקלופרמיד",   2,  date(2026, 11, 30), 0,  False),

    # ── Cardiovascular
    ("Aspirin Cardio",  "אספירין קרדיו",  10, date(2027, 8, 31),  18, False),
    ("Plavix",          "פלוויקס",        3,  date(2027, 4, 30),  18, False),
    ("Atenolol",        "אטנולול",        4,  date(2027, 2, 28),  18, False),
    ("Amlodipine",      "אמלודיפין",      5,  date(2027, 6, 30),  18, False),
    ("Ramipril",        "רמיפריל",        4,  date(2027, 3, 31),  18, False),
    ("Lisinopril",      "ליזינופריל",     3,  date(2027, 1, 31),  18, False),
    ("Furosemide",      "פורוסמיד",       4,  date(2027, 5, 31),  18, False),
    ("Digoxin",         "דיגוקסין",       2,  date(2026, 10, 31), 18, False),
    ("Nitroglycerin",   "ניטרוגליצרין",  3,  date(2026, 8, 31),  18, False),
    ("Warfarin",        "וורפרין",        2,  date(2027, 2, 28),  18, False),

    # ── Diabetes
    ("Metformin",       "מטפורמין",       6,  date(2027, 7, 31),  18, False),
    ("Glucophage",      "גלוקופאג'",      5,  date(2027, 4, 30),  18, False),
    ("Glibenclamide",   "גליבנקלמיד",    3,  date(2027, 2, 28),  18, False),
    ("Januvia",         "ג'נוביה",        2,  date(2027, 6, 30),  18, False),
    ("Insulin",         "אינסולין",       3,  date(2026, 9, 30),  0,  True),

    # ── Dermatology
    ("Betnovate",       "בטנובייט",       4,  date(2027, 3, 31),  2,  False),
    ("Hydrocortisone",  "הידרוקורטיזון",  6,  date(2027, 5, 31),  2,  False),
    ("Elidel",          "אלידל",          3,  date(2027, 1, 31),  3,  False),
    ("Fucidin",         "פוסידין",        4,  date(2027, 4, 30),  0,  True),
    ("Canesten",        "קנסטן",          5,  date(2027, 2, 28),  0,  False),
    ("Nizoral",         "ניזורל",         4,  date(2027, 6, 30),  0,  False),
    ("Lamisil",         "למיזיל",         3,  date(2027, 3, 31),  0,  False),
    ("Zovirax",         "זוביראקס",       3,  date(2027, 1, 31),  0,  False),

    # ── Eye drops
    ("Tobramycin",      "טוברמיצין",      3,  date(2026, 12, 31), 0,  False),
    ("Voltaren Eye",    "וולטרן עיניים",  2,  date(2026, 10, 31), 2,  False),
    ("Refresh",         "ריפרש",          8,  date(2027, 8, 31),  0,  True),
    ("Systane",         "סיסטן",          6,  date(2027, 6, 30),  0,  True),
    ("Alomide",         "אלומייד",        2,  date(2027, 2, 28),  4,  False),

    # ── Vitamins & Supplements
    ("Vitamin C",       "ויטמין C",       15, date(2027, 12, 31), 0,  True),
    ("Vitamin D",       "ויטמין D",       12, date(2027, 10, 31), 0,  True),
    ("Folic Acid",      "חומצה פולית",    10, date(2027, 8, 31),  0,  True),
    ("Iron Tablets",    "טבליות ברזל",    8,  date(2027, 6, 30),  0,  True),
    ("Calcium",         "סידן",           10, date(2027, 9, 30),  0,  True),
    ("Omega 3",         "אומגה 3",        8,  date(2027, 7, 31),  0,  True),
    ("Zinc",            "אבץ",            7,  date(2027, 5, 31),  0,  True),
    ("Magnesium",       "מגנזיום",        6,  date(2027, 4, 30),  0,  True),
    ("Multivitamin",    "מולטי ויטמין",   10, date(2027, 11, 30), 0,  True),
    ("B12",             "ויטמין B12",     8,  date(2027, 8, 31),  0,  True),

    # ── Neurology / Mental health
    ("Carbamazepine",   "קרבמזפין",       2,  date(2027, 3, 31),  0,  False),
    ("Diazepam",        "דיאזפם",         1,  date(2026, 12, 31), 18, False),
    ("Melatonin",       "מלטונין",        8,  date(2027, 6, 30),  0,  False),
    ("Lexapro",         "לקספרו",         2,  date(2027, 4, 30),  18, False),

    # ── Thyroid
    ("Eltroxin",        "אלטרוקסין",      5,  date(2027, 5, 31),  0,  True),
    ("Synthroid",       "סינתרויד",       4,  date(2027, 3, 31),  0,  True),

    # ── Children specific
    ("Nurofen Baby",    "נורופן תינוקות", 5,  date(2027, 2, 28),  0,  False),
    ("Acamol Syrup",    "אקמול סירופ",    6,  date(2027, 4, 30),  0,  False),
    ("Zedex",           "זדקס",           4,  date(2026, 11, 30), 2,  False),
    ("Telfast Junior",  "טלפסט ג'וניור",  3,  date(2027, 1, 31),  6,  False),
    ("Emla",            "אמלה",           3,  date(2027, 6, 30),  0,  False),

    # ── Misc
    ("Voltaren Gel",    "וולטרן ג'ל",     5,  date(2027, 5, 31),  12, False),
    ("Deep Heat",       "דיפ היט",        4,  date(2027, 3, 31),  12, False),
    ("Strepsils",       "סטרפסילס",       8,  date(2027, 7, 31),  6,  True),
    ("Otrivin",         "אוטריבין",       6,  date(2027, 2, 28),  0,  False),
    ("Rhinocort",       "ריינוקורט",      3,  date(2027, 4, 30),  6,  False),
]


def populate():
    created = 0
    skipped = 0

    for name, name_heb, qty, exp, age, pregnant in MEDICINES:
        medicine, was_created = Medicine.objects.get_or_create(
            name=name,
            defaults={
                'name_hebrew':       name_heb,
                'quantity':          qty,
                'expiry_date':       exp,
                'min_age':           age,
                'suitable_pregnant': pregnant,
            }
        )
        if was_created:
            created += 1
            print(f"✅ Added: {name} | {name_heb}")
        else:
            skipped += 1
            print(f"⏭️  Exists: {name} — skipped")

    print(f"\n{'='*40}")
    print(f"✅ Created: {created} medicines")
    print(f"⏭️  Skipped: {skipped} (already exist)")
    print(f"💊 Total in DB: {Medicine.objects.count()}")
    print(f"{'='*40}")


if __name__ == '__main__':
    print("💊 Populating Gemach medicine database...\n")
    populate()
    print("\n🎉 Done!")