# Day 1 video script (2 to 3 minute, one take, no cuts)

## Recording se pehle (5 minute)

1. `python scripts/generate_data.py` chalao taake "aaj" ke orders fresh hon. Answer key screen par aayegi.
2. Sheet mode mein ho to `python scripts/push_to_sheet.py` bhi chalao.
3. Claude Desktop restart karo. Tools icon mein 4 tools dikhne chahiye.
4. Screen layout: left Claude Desktop, right Google Sheet (ya Excel mein `data/orders.csv`).
5. Har sawal ek dafa bina record kiye pooch kar dekh lo. Answer key se match karo.

Answer key (seed 14, kisi bhi din generate karo to yehi counts):

| Sawal | Sahi jawab |
|---|---|
| Total orders | 300 (308 rows, 8 duplicate) |
| Pending | 68 |
| Pending, 3+ din purane | 15 |
| Aaj ke orders | 26 (24 pending) |
| Bilal Ahmed | 9 orders, AG-1001 se AG-1281 |
| Is hafte top item | Lawn 3pc Unstitched (39 units, 12 open orders) |

## Script

**0:00 Intro (15 sec).** Sheet dikhao, scroll karo.
> "Ye ek online clothing store ki order sheet hai. 300 orders, asli jaisa ganda data: duplicate rows,
> khali amounts, phone numbers teen tarah se likhe hue. Owner roz 2 ghante is mein filter lagata hai.
> Dekhte hain Claude se seedha pooch kar kya hota hai."

**0:15 Sawal 1: simple.**
> Type: `Aaj ke pending orders kitne hain aur total value kya hai?`

Tool-call box **expand** karo. Dikhao: `get_orders`, `status: pending`. Bolo:
> "Dekho, Claude ne khud decide kiya ke get_orders call karna hai. Maine ye jawab pehle se nahi likha."

**0:45 Sawal 2: LIVE change (sab se important moment).**
> Type: `Kitne orders 3 din se zyada pending hain?`

Jawab: 15. Ab camera par Sheet mein sab se purane pending order (AG-1052) ka status `delivered` karo.
> Type: `Dobara check karo, ab kitne hain?`

Jawab: 14. Bolo:
> "Maine server restart nahi kiya. Har sawal par data fresh parha jata hai."

**1:15 Sawal 3: customer lookup.**
> Type: `Bilal Ahmed ka order kahan hai?`

`find_order` chalega, 9 orders. Phir phone se:
> Type: `0399-4748855 kis ka number hai aur latest order ka status?`

Bolo: "Sheet mein ye number teen tarah se likha hai. Tool sab match kar leta hai."

**1:45 Sawal 4: CROSS (do tools).**
> Type: `Is hafte sab se zyada kya bika, aur us item ke kitne orders abhi pending hain? Un mein sab se purana kaunsa hai?`

Claude `top_items` phir `get_orders(item=...)` chalayega. Dono tool boxes dikhao. Bolo:
> "Ye sawal Sheet ke filter se nahi hota. Claude ne do tools ko khud joda."

**2:15 Sawal 5: NOT IN DATA (bharosa).**
> Type: `Karachi se kitne orders aaye?`

Claude kahega city ka data nahi hai. Bolo:
> "Ye mera pasandida hissa hai. Data mein city hai hi nahi, aur Claude ne andaza nahi lagaya."

**2:35 Outro (15 sec).** VS Code mein `server.py` 5 second dikhao, phir GitHub repo.
> "Poora server 400 se kam lines Python hai, read-only, kuch delete ya change nahi kar sakta.
> Code aur 5 minute setup description mein hai. Ye Day 1 of 14 hai, kal COD returns analytics."

## Proof checklist (upload se pehle tick karo)

- [ ] Live data change camera par, jawab badla
- [ ] Kam se kam 2 tool-call boxes expanded
- [ ] Ek cross-tool sawal
- [ ] Ek "data mein nahi hai" sawal
- [ ] Koi cut nahi, 3 minute se kam
- [ ] End mein code + GitHub link
