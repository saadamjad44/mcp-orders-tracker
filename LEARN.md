# Day 1: MCP ko samajhna (sirf banana nahi)

Ye file tumhare liye hai, GitHub ke liye nahi. Aaj ka concept: **MCP basics, stdio transport,
aur Claude tool kaise chunta hai.** Isay parh kar `server.py` kholo aur saath saath dekho.

## 1. MCP ek line mein

MCP ek standard hai jis se Claude tumhare code ke functions call kar sakta hai.
Tum ne AI nahi banaya. Tum ne Claude ko client ke data tak ek rasta diya.

Ek MCP server teen cheezein de sakta hai:

| Cheez | Kya hai | Aaj use hui? |
|---|---|---|
| **Tools** | Functions jo Claude khud call karta hai (parameters ke saath) | Haan, 4 tools |
| **Resources** | Data jo user Claude ke context mein attach karta hai | Nahi, Day 4 |
| **Prompts** | Tayyar prompt templates, slash command jaise | Nahi, Day 5 |

## 2. server.py ka naqsha (upar se neeche)

1. **Imports aur logging.** `logging.basicConfig(stream=sys.stderr)`. Ye line bohat zaroori hai, neeche wajah.
2. **`mcp = MCPServer("ahmed-garments-orders", instructions=...)`.** Server ka naam, aur `instructions`
   jo Claude ko batati hain data mein kya hai aur kya nahi.
3. **Config (.env).** `DATA_SOURCE=csv` ya `sheets`. Code same, sirf data ka source badalta hai.
4. **`_read_csv()` aur `_read_sheet()`.** Kachcha data laate hain. Har tool call par dobara parha jata hai,
   isi liye Sheet mein change karo to agla jawab badal jata hai.
5. **`load_orders()`.** Safai: duplicate rows hatana, phone normalise, status lowercase, amount number.
6. **4 `@mcp.tool()` functions.** Yahi wo cheez hai jo Claude dekhta hai.
7. **`mcp.run()`.** Server shuru, stdio par.

## 3. Ek sawal ka poora safar (6 steps)

User likhta hai: "3 din se zyada purane pending orders dikhao"

1. Claude Desktop ne startup par tumhari script chalayi thi aur tools ki list li thi:
   har tool ka **naam, description, aur argument schema**.
2. Claude sawal parhta hai aur descriptions se match karta hai. `get_orders` ki description mein
   likha hai "which orders are pending for more than 3 days", to wo yehi chunta hai.
3. Claude arguments banata hai: `{"status": "pending", "days_old": 3}`. Ye schema se aata hai,
   jo tumhare type hints (`status: str`, `days_old: int`) se bana.
4. Claude Desktop ye call JSON message ki shakal mein tumhari script ke **stdin** par bhejta hai.
5. Tumhara function chalta hai, data parhta hai, dict return karta hai. SDK usay JSON bana kar
   **stdout** par wapas bhejta hai.
6. Claude JSON parhta hai aur insani zabaan mein jawab likhta hai.

Tum ne sirf step 5 likha. Baaki sab protocol aur Claude karta hai.

## 4. Do rules jo yaad rakhne hain

**Rule 1: stdout par kabhi print() nahi.**
stdio transport mein stdout sirf MCP messages ke liye hai. Agar tum `print("hello")` karo to
wo protocol ke beech mein ghus jata hai aur connection toot jata hai. Debug ke liye `log.info(...)`
use karo, jo stderr par jata hai. Claude Desktop stderr ko log file mein save karta hai.

**Rule 2: jo error Claude ko dikhana ho, `ToolError` raise karo.**
Ye aaj test mein pakda gaya. SDK v2 mein:

- `raise ToolError("Unknown status 'lost'. Use one of: ...")` : Claude ko poora message milta hai,
  wo apni call theek kar leta hai ya user ko bata deta hai.
- `raise ValueError(...)` ya koi aur exception: SDK isay crash samajhta hai. Claude ko sirf
  "Error executing tool get_orders" milta hai, asli wajah chhup jati hai.

Client ke liye iska matlab: achha error message = Claude khud masla samjha deta hai, tumhe call nahi aati.

## 5. Sab se important cheez: description

Claude code nahi parhta. Wo sirf **docstring** parhta hai. Achhi description teen sawalon ka jawab deti hai:

1. Tool kya return karta hai?
2. Kab use karna hai? (example sawalon ke saath)
3. Har argument ka exact format kya hai? (`YYYY-MM-DD`, allowed values ki list)

### Aaj ka experiment (15 minute, zaroor karo)

1. `server.py` mein `find_order` ki docstring ko badal kar sirf `"""Gets data."""` kar do.
2. Claude Desktop restart karo. Pucho: "Bilal Ahmed ka order kahan hai?"
3. Dekho Claude kya karta hai. Aksar wo `get_orders` se saare orders mangwa kar khud dhoondta hai,
   ya galat tool chunta hai.
4. Docstring wapas theek karo, restart, dobara pucho. Ab seedha `find_order` chalega.

Ye farq apni aankhon se dekhna hi Day 1 ka asli sabaq hai. Video mein bhi ek line bolo:
"Tool ka code same hai, sirf description badli, aur Claude ka behaviour badal gaya."

## 6. SDK v2 note (plan mein jo badla)

Internet par zyada tar tutorials aur meri pehli example `from mcp.server.fastmcp import FastMCP`
likhti hain. Ye purana (v1) hai. Install hone wala version 2.x hai, jahan:

| v1 (purana) | v2 (jo hum use kar rahe hain) |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| `FastMCP("name")` | `MCPServer("name")` |
| Koi bhi exception ka message Claude ko jata tha | Sirf `ToolError` ka message jata hai |

Decorators (`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`) aur `mcp.run()` wahi hain.
Agar kisi client ka purana server `FastMCP` use karta ho, to ye migration khud ek chhoti paid gig hai.

## 7. Debug kaise karein

- **Claude ke bagair test:** `python scripts/test_client.py`. Ye wohi karta hai jo Claude Desktop karta hai.
- **Browser mein tools chalana:** `npx @modelcontextprotocol/inspector D:\MCP-14\venv\Scripts\python.exe server.py`
- **Seedha chalana:** `python server.py`. Agar import error ho to yahin dikh jayega. (Chalne ke baad wo input ka wait karega, Ctrl+C se band karo.)
- **Claude Desktop logs:** Settings > Developer > Open Logs Folder.

## 8. Khud se 5 sawal (bina dekhe jawab do, phir LOG.md mein likho)

1. Claude ko kaise pata chalta hai ke kaunsa tool call karna hai?
2. stdio transport mein `print()` kyun mana hai?
3. Sheet mein change karne ke baad server restart kyun nahi karna padta?
4. `ToolError` aur `ValueError` mein Claude ke liye kya farq hai?
5. Client ko ek minute mein kaise samjhaoge ke ye system unka data "train" nahi karta, sirf parhta hai?
