"""Day 1/14 - Orders Tracker MCP server for a small online clothing store.

Lets Claude answer questions about orders that live in a Google Sheet (or a CSV):
"which orders are still pending?", "where is Bilal Ahmed's order?", "how was today?"

Read-only: this server cannot change or delete anything.

How it works (stdio transport):
  Claude Desktop starts this script and exchanges JSON messages over stdin/stdout.
  On startup the server sends the list of tools (name + description + argument schema).
  Claude reads those descriptions to decide which tool to call, so they matter more
  than the code underneath.

Uses the MCP Python SDK v2 (MCPServer; it was called FastMCP in v1).
"""
from __future__ import annotations

import csv
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Errors: raise ToolError for a failure you expect (bad input, missing file). Its
# message is sent to Claude, so Claude can fix the call or explain it to the user.
# Any other exception is treated as a crash: Claude only sees "Error executing tool".

# stdout is reserved for the MCP protocol, so all logging goes to stderr.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("orders")

mcp = MCPServer(
    "ahmed-garments-orders",
    instructions=(
        "Read-only access to the order sheet of Ahmed Garments, a small online clothing store. "
        "Amounts are in PKR. The data has these fields only: order_id, order_date, customer_name, "
        "phone, item, size, qty, amount, status, courier, note. There is no city, address, "
        "payment-method or customer-age field: if a question needs one, say it is not in the data "
        "instead of guessing."
    ),
)
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)

STATUSES = ["pending", "shipped", "delivered", "returned", "cancelled", "address incomplete"]
FIELDS = ["order_id", "order_date", "customer_name", "phone", "item", "size",
          "qty", "amount", "status", "courier", "note"]


# ----------------------------------------------------------------------------
# Configuration (.env)
# ----------------------------------------------------------------------------
def env_path(name: str, default: str) -> Path:
    """Read a path from .env. Relative paths are resolved from this folder."""
    p = Path(os.getenv(name, default))
    return p if p.is_absolute() else BASE_DIR / p


DATA_SOURCE = os.getenv("DATA_SOURCE", "csv").strip().lower()   # "csv" or "sheets"
ORDERS_CSV = env_path("ORDERS_CSV", "data/orders.csv")
GOOGLE_CREDS = env_path("GOOGLE_CREDS", "data/creds.json")
SHEET_ID = os.getenv("SHEET_ID", "").strip()
WORKSHEET = os.getenv("WORKSHEET", "Orders").strip()

_gspread_client = None  # created once, reused for every call


# ----------------------------------------------------------------------------
# Reading the raw rows. Data is read fresh on every tool call, so an edit in the
# sheet shows up in the very next answer.
# ----------------------------------------------------------------------------
def _read_csv() -> list[dict]:
    if not ORDERS_CSV.exists():
        raise ToolError(
            f"Orders file not found: {ORDERS_CSV}. Run 'python scripts/generate_data.py' first."
        )
    with ORDERS_CSV.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _read_sheet() -> list[dict]:
    global _gspread_client
    if not SHEET_ID:
        raise ToolError("SHEET_ID is empty in .env. Put the id from the sheet URL there.")
    if not GOOGLE_CREDS.exists():
        raise ToolError(
            f"Google credentials file not found: {GOOGLE_CREDS}. "
            "Download the service-account JSON key and save it there."
        )
    try:
        import gspread

        if _gspread_client is None:
            _gspread_client = gspread.service_account(filename=str(GOOGLE_CREDS))
        worksheet = _gspread_client.open_by_key(SHEET_ID).worksheet(WORKSHEET)
        # numericise_ignore keeps everything as text, so phone 0380... keeps its zero.
        return worksheet.get_all_records(numericise_ignore=["all"])
    except Exception as exc:  # turn any Google error into a message a human can act on
        log.exception("Google Sheet read failed")
        raise ToolError(
            f"Could not read the Google Sheet ({type(exc).__name__}: {exc}). "
            "Check that the sheet is shared with the service-account email, that SHEET_ID is "
            f"correct, and that a tab named '{WORKSHEET}' exists."
        ) from exc


# ----------------------------------------------------------------------------
# Cleaning. Real sheets are messy, so every value is normalised before use.
# ----------------------------------------------------------------------------
def _digits(raw) -> str:
    """Phone as 10 digits without country code or leading zero: 3801234567."""
    d = re.sub(r"\D", "", str(raw or ""))
    if d.startswith("0092"):
        d = d[4:]
    elif d.startswith("92") and len(d) == 12:
        d = d[2:]
    return d.lstrip("0")


def _to_date(raw) -> date | None:
    text = str(raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _to_int(raw) -> int | None:
    text = re.sub(r"[^\d.]", "", str(raw or ""))
    try:
        return int(float(text)) if text else None
    except ValueError:
        return None


def load_orders() -> tuple[list[dict], dict]:
    """Return (clean orders, data-quality report)."""
    raw_rows = _read_sheet() if DATA_SOURCE == "sheets" else _read_csv()
    quality = {"duplicate_rows_ignored": 0, "orders_missing_amount": 0,
               "orders_with_unreadable_date": 0, "blank_rows_skipped": 0}
    orders, seen = [], set()
    for raw in raw_rows:
        row = {str(k).strip().lower(): ("" if v is None else str(v).strip()) for k, v in raw.items()}
        order_id = row.get("order_id", "").upper()
        if not order_id:
            quality["blank_rows_skipped"] += 1
            continue
        if order_id in seen:                      # same order typed twice
            quality["duplicate_rows_ignored"] += 1
            continue
        seen.add(order_id)

        amount = _to_int(row.get("amount"))
        order_date = _to_date(row.get("order_date"))
        if amount is None:
            quality["orders_missing_amount"] += 1
        if order_date is None:
            quality["orders_with_unreadable_date"] += 1

        orders.append({
            "order_id": order_id,
            "order_date": order_date.isoformat() if order_date else None,
            "customer_name": " ".join(row.get("customer_name", "").split()).title(),
            "phone": row.get("phone", ""),
            "item": row.get("item", ""),
            "size": row.get("size", ""),
            "qty": _to_int(row.get("qty")) or 1,
            "amount": amount,
            "status": " ".join(row.get("status", "").lower().split()) or "unknown",
            "courier": row.get("courier", ""),
            "note": row.get("note", ""),
            "_date": order_date,                  # private helpers, removed before returning
            "_phone": _digits(row.get("phone")),
        })
    log.info("Loaded %d orders from %s", len(orders), DATA_SOURCE)
    return orders, quality


def _public(order: dict, today: date) -> dict:
    out = {k: v for k, v in order.items() if not k.startswith("_")}
    out["days_old"] = (today - order["_date"]).days if order["_date"] else None
    return out


def _is_open(order: dict) -> bool:
    return order["status"] in ("pending", "address incomplete")


# ----------------------------------------------------------------------------
# Tools. The docstring IS the description Claude reads.
# ----------------------------------------------------------------------------
@mcp.tool(annotations=READ_ONLY)
def get_orders(status: str = "all", days_old: int = 0, item: str = "", limit: int = 50) -> dict:
    """List orders, with optional filters. Use for "show pending orders",
    "which orders are pending for more than 3 days", "pending orders for kurta".

    Returns total_matching (the full count) plus up to `limit` orders. Each order
    includes days_old (age in days). Read fresh from the sheet on every call.

    Args:
        status: One of: all, pending, shipped, delivered, returned, cancelled, address incomplete.
        days_old: Only orders at least this many days old. 0 = no age filter.
            Example: days_old=3 means the order was placed 3 or more days ago.
        item: Part of an item name, case-insensitive, e.g. "kurta". Empty = all items.
        limit: Maximum orders to return (default 50, maximum 200).
    """
    status = " ".join(status.lower().split())
    if status != "all" and status not in STATUSES:
        raise ToolError(f"Unknown status '{status}'. Use one of: all, {', '.join(STATUSES)}.")
    limit = max(1, min(int(limit), 200))
    today = date.today()
    orders, quality = load_orders()

    matches = orders
    if status != "all":
        matches = [o for o in matches if o["status"] == status]
    if days_old > 0:
        cutoff = today - timedelta(days=days_old)
        matches = [o for o in matches if o["_date"] and o["_date"] <= cutoff]
    if item.strip():
        needle = item.strip().lower()
        matches = [o for o in matches if needle in o["item"].lower()]

    # Age filter -> oldest first (most urgent). Otherwise newest first.
    matches.sort(key=lambda o: o["_date"] or date.min, reverse=(days_old == 0))
    return {
        "as_of": today.isoformat(),
        "filters": {"status": status, "days_old": days_old, "item": item},
        "total_matching": len(matches),
        "showing": min(len(matches), limit),
        "total_amount_pkr": sum(o["amount"] or 0 for o in matches),
        "orders": [_public(o, today) for o in matches[:limit]],
        "data_quality": quality,
    }


@mcp.tool(annotations=READ_ONLY)
def find_order(query: str) -> dict:
    """Find orders by order id, phone number, or customer name. Use for
    "where is order AG-1042?", "status of 0380-1234567", "where is Bilal Ahmed's order?".

    Args:
        query: An order id (AG-1042), a phone number in any format
            (03801234567, 0380-1234567, +923801234567), or a full or partial customer name.
    """
    text = query.strip()
    if not text:
        raise ToolError("query is empty. Give an order id, a phone number, or a customer name.")
    today = date.today()
    orders, _ = load_orders()

    id_match = re.fullmatch(r"([A-Za-z]+)[-\s]?(\d+)", text)
    digits = re.sub(r"\D", "", text)
    if id_match:
        matched_by = "order_id"
        wanted = f"{id_match.group(1).upper()}-{id_match.group(2)}"
        found = [o for o in orders if o["order_id"] == wanted]
    elif len(digits) >= 7:
        matched_by = "phone"
        wanted = _digits(text)
        found = [o for o in orders if o["_phone"] and o["_phone"].endswith(wanted)]
    else:
        matched_by = "customer_name"
        words = text.lower().split()
        found = [o for o in orders if all(w in o["customer_name"].lower() for w in words)]

    found.sort(key=lambda o: o["_date"] or date.min, reverse=True)
    result = {"query": query, "matched_by": matched_by, "count": len(found),
              "orders": [_public(o, today) for o in found[:25]]}
    if not found:
        result["message"] = (f"No order found for '{query}'. "
                             "Searched order_id, phone and customer_name.")
    return result


@mcp.tool(annotations=READ_ONLY)
def daily_summary(day: str = "today") -> dict:
    """Summary of one day's orders: how many, by status, order value, top item.
    Use for "how was today?", "yesterday's summary", "orders on 2026-11-10".

    Args:
        day: "today", "yesterday", or a date as YYYY-MM-DD.
    """
    today = date.today()
    key = day.strip().lower()
    if key == "today":
        target = today
    elif key == "yesterday":
        target = today - timedelta(days=1)
    else:
        target = _to_date(day)
        if target is None:
            raise ToolError(f"Could not read the date '{day}'. Use today, yesterday, or YYYY-MM-DD.")

    orders, quality = load_orders()
    rows = [o for o in orders if o["_date"] == target]
    if not rows:
        dates = [o["_date"] for o in orders if o["_date"]]
        return {"date": target.isoformat(), "total_orders": 0,
                "message": (f"No orders on {target.isoformat()}. "
                            f"The sheet covers {min(dates)} to {max(dates)}." if dates else "The sheet is empty.")}

    live = [o for o in rows if o["status"] not in ("cancelled", "returned")]
    item_qty = Counter()
    for o in live:
        item_qty[o["item"]] += o["qty"]
    return {
        "date": target.isoformat(),
        "total_orders": len(rows),
        "by_status": dict(Counter(o["status"] for o in rows).most_common()),
        "order_value_pkr": sum(o["amount"] or 0 for o in live),
        "order_value_note": "Excludes cancelled and returned orders. Orders with a blank amount count as 0.",
        "delivered_value_pkr": sum(o["amount"] or 0 for o in rows if o["status"] == "delivered"),
        "orders_missing_amount": sum(o["amount"] is None for o in rows),
        "top_item": item_qty.most_common(1)[0][0] if item_qty else None,
        "data_quality": quality,
    }


@mcp.tool(annotations=READ_ONLY)
def top_items(days: int = 7, limit: int = 5) -> dict:
    """Best-selling items in the last N days, ranked by units sold. For each item also
    returns how many of its orders are still open (pending or address incomplete).
    Use for "what is selling best this week?", "top 3 items this month".

    Args:
        days: Look back this many days, counting today (default 7; 30 = about a month).
        limit: How many items to return (default 5).
    """
    days = max(1, int(days))
    limit = max(1, min(int(limit), 50))
    today = date.today()
    start = today - timedelta(days=days - 1)
    orders, quality = load_orders()

    stats = defaultdict(lambda: {"units_sold": 0, "orders": 0, "value_pkr": 0, "open_orders": 0})
    for o in orders:
        if not o["_date"] or not (start <= o["_date"] <= today) or o["status"] == "cancelled":
            continue
        s = stats[o["item"]]
        s["units_sold"] += o["qty"]
        s["orders"] += 1
        s["value_pkr"] += o["amount"] or 0
        s["open_orders"] += _is_open(o)

    ranked = sorted(stats.items(), key=lambda kv: (-kv[1]["units_sold"], kv[0]))
    return {
        "period": {"from": start.isoformat(), "to": today.isoformat(), "days": days},
        "note": "Cancelled orders are excluded.",
        "items": [{"rank": i + 1, "item": name, **s} for i, (name, s) in enumerate(ranked[:limit])],
        "data_quality": quality,
    }


if __name__ == "__main__":
    log.info("Starting orders server (source=%s)", DATA_SOURCE)
    mcp.run()  # stdio: Claude Desktop launches this script and talks over stdin/stdout
