"""End-to-end check without Claude: start server.py over stdio and call every tool.

Usage:  python scripts/test_client.py
This is exactly what Claude Desktop does: launch the script, list tools, call them.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).resolve().parent.parent / "server.py"

CALLS = [
    ("get_orders", {"status": "pending", "limit": 2}),
    ("get_orders", {"status": "pending", "days_old": 3, "limit": 2}),
    ("get_orders", {"status": "pending", "item": "kurta", "limit": 1}),
    ("find_order", {"query": "Bilal Ahmed"}),
    ("find_order", {"query": "ag1001"}),
    ("find_order", {"query": "no such customer"}),
    ("daily_summary", {"day": "today"}),
    ("top_items", {"days": 7, "limit": 3}),
    ("get_orders", {"status": "lost"}),          # should fail with a clear message
]


def text_of(result) -> str:
    return "\n".join(getattr(block, "text", str(block)) for block in result.content)


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with Client(params) as client:
        tools = (await client.list_tools()).tools
        print(f"Server exposes {len(tools)} tool(s):")
        for tool in tools:
            first_line = (tool.description or "").strip().splitlines()[0]
            print(f"  - {tool.name}: {first_line}")
        for name, args in CALLS:
            result = await client.call_tool(name, args)
            flag = "ERROR" if getattr(result, "is_error", False) else "ok"
            print(f"\n>>> {name}({args})  [{flag}]")
            print(text_of(result)[:900])


if __name__ == "__main__":
    asyncio.run(main())
