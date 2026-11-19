# YouTube and LinkedIn text for Day 1

## YouTube

**Title**

MCP Day 1/14: Ask Claude About Your Orders in Google Sheets (Custom MCP Server, Python)

**Description**

I am building 14 MCP servers in 14 days. Day 1: an Orders Tracker that connects Claude to a small
online store's order sheet.

In this one-take demo, Claude:
- lists pending orders from live data
- picks up a change I make in the sheet on camera
- finds a customer by name or phone number
- combines two tools to answer one question
- says "that is not in the data" instead of guessing

Read-only. Under 400 lines of Python. Built with the MCP Python SDK v2.

Code and 5-minute setup: <GitHub repo link>

0:00 The messy order sheet
0:15 Pending orders
0:45 Live data change
1:15 Find a customer
1:45 Two tools, one question
2:15 A question the data cannot answer
2:35 The code

**Tags**

mcp server, model context protocol, claude ai, claude desktop, python, google sheets, ai automation, ai agent

**Playlist**

14 MCPs in 14 Days

## LinkedIn post

Day 1 of 14: I am building one MCP server every day.

Today: an Orders Tracker for a small online clothing store.

The owner keeps 300 orders in a Google Sheet and spends two hours a day filtering it to answer
"where is my order?" on WhatsApp.

Now they type the question into Claude:
"Which orders have been pending for more than 3 days?"

Claude calls a tool I wrote, reads the live sheet, and answers. I change a row on camera,
ask again, and the number changes. When I ask about cities, which the sheet does not have,
it says so instead of guessing.

What I learned today: Claude never reads your code. It reads the tool description.
Same code with a vague description, and it picks the wrong tool.

One-take demo in the video. Code is open source, link in the comments.

Tomorrow: cash-on-delivery returns analytics by courier.

#MCP #ClaudeAI #Python #AIAutomation #BuildInPublic

(First comment: GitHub repo link + YouTube link)
