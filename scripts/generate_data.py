"""Generate realistic, slightly messy order data for "Ahmed Garments".

Usage:
    python scripts/generate_data.py            # 300 orders ending today
    python scripts/generate_data.py --seed 7   # a different but repeatable set

Run it again on the day you record the video, so "today" has fresh orders.

The mess is deliberate (it is what real sheets look like):
  - a few duplicate rows (double entry)
  - a few blank amounts
  - status typed in different cases, with stray spaces
  - phone numbers typed three different ways
  - a few dates typed as dd/mm/yyyy
There is NO city column on purpose: the demo asks about cities to show that the
assistant says "that is not in the data" instead of guessing.
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COLUMNS = ["order_id", "order_date", "customer_name", "phone", "item", "size",
           "qty", "amount", "status", "courier", "note"]

FIRST_NAMES = [
    "Ayesha", "Bilal", "Hassan", "Fatima", "Usman", "Zainab", "Ali", "Maryam", "Hamza", "Sana",
    "Ahmed", "Hira", "Imran", "Nida", "Saad", "Rabia", "Kamran", "Amna", "Faisal", "Sadia",
    "Tariq", "Mehwish", "Junaid", "Iqra", "Waqas", "Noor", "Shahid", "Kiran", "Adnan", "Bushra",
    "Rizwan", "Aliya", "Farhan", "Samina", "Danish", "Mahnoor", "Asad", "Laiba", "Naveed", "Anum",
]
LAST_NAMES = [
    "Malik", "Ahmed", "Raza", "Noor", "Tariq", "Khan", "Hussain", "Sheikh", "Butt", "Chaudhry",
    "Qureshi", "Iqbal", "Siddiqui", "Aslam", "Javed", "Mirza", "Rehman", "Shah", "Akhtar", "Baig",
]

# Prefixes 0380-0399 are used on purpose: as far as we know they are not assigned
# to any operator, so no real person's number shows up in a public demo video.
PHONE_PREFIXES = [f"03{n}" for n in range(80, 100)]

# (item, unit price in PKR, sizes, popularity weight)
ITEMS = [
    ("Lawn 3pc Unstitched", 4500, ["Free"], 16),
    ("Embroidered Kurta", 2800, ["S", "M", "L", "XL"], 13),
    ("Plain Cotton Kurta", 1900, ["S", "M", "L", "XL"], 11),
    ("Shalwar Kameez (Men)", 3900, ["S", "M", "L", "XL"], 9),
    ("Khaddar 3pc Unstitched", 5200, ["Free"], 8),
    ("Lawn 2pc Unstitched", 3200, ["Free"], 8),
    ("Kids Kurta Shalwar", 2200, ["2-3Y", "4-5Y", "6-7Y", "8-9Y"], 7),
    ("Khussa (Ladies)", 1800, ["36", "37", "38", "39", "40"], 6),
    ("Chiffon Dupatta", 1500, ["Free"], 6),
    ("Printed Shawl", 2400, ["Free"], 5),
    ("Waistcoat", 3500, ["S", "M", "L", "XL"], 4),
    ("Peshawari Chappal", 3200, ["40", "41", "42", "43", "44"], 4),
    ("Linen Trousers", 2100, ["S", "M", "L", "XL"], 2),
    ("Bridal Clutch", 2600, ["Free"], 1),
]
COURIERS = ["TCS", "Leopards", "M&P", "PostEx"]
DELIVERY_CHARGE = 200

# How likely each status is, depending on how old the order is.
STATUS_BY_AGE = [
    (0, {"pending": 85, "address incomplete": 5, "cancelled": 5, "shipped": 5}),
    (2, {"pending": 45, "shipped": 40, "address incomplete": 5, "cancelled": 5, "delivered": 5}),
    (6, {"shipped": 30, "delivered": 45, "pending": 12, "returned": 6, "cancelled": 4,
         "address incomplete": 3}),
    (999, {"delivered": 78, "returned": 10, "cancelled": 5, "pending": 4, "shipped": 3}),
]
NOTES = {
    "pending_old": ["customer not answering", "call again tomorrow", "waiting for stock",
                    "customer asked to delay"],
    "pending_new": ["", "", "", "call before delivery", "gift wrap"],
    "address incomplete": ["house number missing", "area name unclear", "asked customer on WhatsApp"],
    "returned": ["customer refused", "size issue", "not at home 3 attempts", "wrong item sent"],
    "cancelled": ["customer cancelled", "duplicate order", "out of stock"],
    "other": ["", "", "", "", "call before delivery"],
}


def weighted(rng: random.Random, table: dict[str, int]) -> str:
    return rng.choices(list(table), weights=list(table.values()))[0]


def messy_phone(phone: str, rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.60:
        return phone
    if roll < 0.85:
        return f"{phone[:4]}-{phone[4:]}"
    return "+92" + phone[1:]


def make_customers(rng: random.Random, n: int = 130) -> list[tuple[str, str]]:
    # Two fixed customers so the demo questions always have an answer.
    names = ["Bilal Ahmed", "Ayesha Malik"]
    while len(names) < n:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in names:
            names.append(name)
    return [(name, rng.choice(PHONE_PREFIXES) + f"{rng.randint(0, 9_999_999):07d}") for name in names]


def make_orders(today: date, n: int, rng: random.Random) -> list[dict]:
    customers = make_customers(rng)
    # More recent orders than old ones; oldest order gets the lowest order number.
    ages = sorted((min(int(rng.expovariate(1 / 9)), 34) for _ in range(n)), reverse=True)
    item_weights = [w for *_, w in ITEMS]

    rows = []
    for i, age in enumerate(ages):
        # The two demo customers get the first few orders, everyone else is random.
        name, phone = customers[i % 2] if i % 40 < 2 else rng.choice(customers)
        item, price, sizes, _ = rng.choices(ITEMS, weights=item_weights)[0]
        qty = rng.choices([1, 2, 3], weights=[75, 20, 5])[0]
        table = next(t for max_age, t in STATUS_BY_AGE if age <= max_age)
        status = weighted(rng, table)

        if status == "pending":
            note = rng.choice(NOTES["pending_old" if age >= 3 else "pending_new"])
        else:
            note = rng.choice(NOTES.get(status, NOTES["other"]))
        courier = rng.choice(COURIERS) if status in ("shipped", "delivered", "returned") else ""
        order_date = today - timedelta(days=age)

        rows.append({
            "order_id": f"AG-{1001 + i}",
            "order_date": order_date.isoformat(),
            "customer_name": name,
            "phone": messy_phone(phone, rng),
            "item": item,
            "size": rng.choice(sizes),
            "qty": qty,
            "amount": price * qty + DELIVERY_CHARGE,
            "status": status,
            "courier": courier,
            "note": note,
        })
    return rows


def add_mess(rows: list[dict], rng: random.Random) -> dict[str, int]:
    """Make the sheet look like real staff typed it. Returns what was changed."""
    report = Counter()
    for row in rows:
        if rng.random() < 0.03:
            row["amount"] = ""
            report["blank_amounts"] += 1
        if rng.random() < 0.06:
            row["status"] = rng.choice([row["status"].title(), row["status"].upper(), row["status"] + " "])
            report["odd_status_typing"] += 1
        if rng.random() < 0.04:
            row["customer_name"] = rng.choice([row["customer_name"].lower(), "  " + row["customer_name"]])
            report["odd_name_typing"] += 1
        if rng.random() < 0.03:
            y, m, d = row["order_date"].split("-")
            row["order_date"] = f"{d}/{m}/{y}"
            report["dd_mm_yyyy_dates"] += 1
    # Double entry: copy a few rows right below the original.
    for index in sorted(rng.sample(range(len(rows)), k=8), reverse=True):
        rows.insert(index + 1, dict(rows[index]))
        report["duplicate_rows"] += 1
    return dict(report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument("--orders", type=int, default=300)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    today = date.today()
    rows = make_orders(today, args.orders, rng)

    # Answer key, computed on the clean data before the mess is added.
    by_status = Counter(r["status"] for r in rows)
    todays = [r for r in rows if r["order_date"] == today.isoformat()]
    pending_today = sum(r["status"] == "pending" for r in todays)
    late_pending = len([r for r in rows if r["status"] == "pending"
                        and (today - date.fromisoformat(r["order_date"])).days >= 3])
    bilal = [r["order_id"] for r in rows if r["customer_name"] == "Bilal Ahmed"]
    orders_today = len(todays)

    mess = add_mess(rows, rng)

    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "orders.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {path}  ({len(rows)} rows = {args.orders} orders + {mess['duplicate_rows']} duplicates)")
    print(f"today is {today.isoformat()}")
    print("ANSWER KEY (use it to check Claude's answers before recording):")
    print(f"  orders by status : {dict(by_status.most_common())}")
    print(f"  orders today     : {orders_today}  (pending today: {pending_today})")
    print(f"  pending 3+ days  : {late_pending}")
    print(f"  Bilal Ahmed      : {len(bilal)} orders -> {', '.join(bilal)}")
    print(f"  mess added       : {mess}")


if __name__ == "__main__":
    main()
