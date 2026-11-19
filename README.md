# Orders Tracker MCP  (Day 1/14)

Ask your order sheet questions in plain language inside Claude. No dashboards, no manual filtering.

Built for a small online clothing store that keeps its orders in Google Sheets and answers
"where is my order?" on WhatsApp all day.

**Demo video:** _add YouTube link_

## What you can ask

- "Show today's pending orders."
- "Which orders have been pending for more than 3 days?"
- "Where is Bilal Ahmed's order?" or "Status of 0399-4748855?"
- "What sold best this week, and how many of those orders are still open?"
- "How was yesterday?"

Claude reads the sheet fresh on every question. Change a status in the sheet, ask again, and the answer changes.

## Tools

| Tool | What it returns |
|---|---|
| `get_orders(status, days_old, item, limit)` | Orders filtered by status, age and item, with the full count |
| `find_order(query)` | Orders by order id, phone number (any format) or customer name |
| `daily_summary(day)` | One day's orders: count, by status, order value, top item |
| `top_items(days, limit)` | Best sellers in the last N days, with open orders per item |

Every tool is marked read-only. This server cannot change or delete anything.

It also handles messy data the way real sheets need: duplicate rows are ignored and reported,
blank amounts are counted, phone numbers match in any format, and status typing like
`Pending ` or `DELIVERED` is normalised.

## Run it yourself (5 minutes)

Requires Python 3.10 or newer.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/generate_data.py
python scripts/test_client.py
```

`generate_data.py` writes 300 realistic orders to `data/orders.csv` and prints an answer key.
`test_client.py` starts the server and calls every tool, exactly as Claude Desktop would.

### Connect to Claude Desktop

Claude Desktop > Settings > Developer > Edit Config, then add this server
(use your own paths, with double backslashes):

```json
{
  "mcpServers": {
    "ahmed-garments-orders": {
      "command": "D:\\MCP-14\\venv\\Scripts\\python.exe",
      "args": ["D:\\MCP-14\\day01-orders\\server.py"]
    }
  }
}
```

Quit Claude Desktop from the system tray and open it again. The four tools appear under the tools icon.

### Google Sheets mode

1. In Google Cloud Console, create a project, enable the **Google Sheets API**, create a **service account**, and download its JSON key to `data/creds.json`.
2. Create an empty Google Sheet and share it with the service-account email as **Editor**.
3. In `.env`, set `SHEET_ID` to the id in the sheet URL (the long part between `/d/` and `/edit`).
4. Upload the sample data: `python scripts/push_to_sheet.py`
5. In `.env`, set `DATA_SOURCE=sheets`, then restart Claude Desktop.

After uploading, you can lower the service account to **Viewer**. The server only reads.

## Troubleshooting

- **Tools do not appear:** edit the config only while Claude Desktop is fully closed. The app rewrites this file while it runs, so an entry added with the app open can be wiped. Quit from the tray, edit, then reopen. Also check both paths and use double backslashes.
- **Server crashes on start:** run `python server.py` in a terminal and read the error.
- **Logs:** Claude Desktop > Settings > Developer > Open Logs Folder, file `mcp-server-ahmed-garments-orders.log`.
- **"Orders file not found":** run `python scripts/generate_data.py`.
- **"Could not read the Google Sheet":** the sheet is not shared with the service-account email, or `SHEET_ID` is wrong, or the tab is not named `Orders`.
- **No orders "today":** the sample data is dated relative to the day you generated it. Run `generate_data.py` again.

## How it works

Claude Desktop starts `server.py` and talks to it over stdin/stdout (the MCP stdio transport).
The server announces its tools with a name, a description and an argument schema.
Claude reads those descriptions to decide which tool to call, the server fetches the rows,
and Claude writes the answer. Built with the MCP Python SDK v2 (`MCPServer`).

## License

MIT
