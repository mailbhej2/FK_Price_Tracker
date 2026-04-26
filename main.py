import asyncio,os
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8654703995:AAGQ0STYEcXZe1Ca5Lh4647TnH3T7Apwlag" # os.getenv("BOT_TOKEN")
CHAT_ID = "266428657"

URL = None
THRESHOLD = None
LAST_SENT = None

def format_price(price):
    return int(price.replace("₹", "").replace(",", "").strip())


async def get_price():
    if not URL:
        return None, None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()

        await page.goto(URL)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        await browser.close()

        tree = HTMLParser(html)

        try:
            base_price = tree.css_first(
                '.v1zwn21l.v1zwn20._1psv1zeb9._1psv1ze0'
            ).text(strip=True)

            for node in tree.css("div"):
                if node.text(strip=True) == "Lowest price for you":
                    parent = node.parent
                    price_text = parent.text().replace("Lowest price for you","").strip()
                    #print("text",price_text)

                    # --- your logic (kept) ---
                    if price_text.count("₹") > 2:
                        prices = [x for x in price_text.split() if "₹" in x]
                        off_price = prices[0]
                    else:
                        off_price = price_text

                    if not off_price:
                        return base_price, 0

                    bank_discount = format_price(base_price) - format_price(off_price)

                    return base_price, bank_discount

        except:
            pass

        return None, None


# ----------- SET LINK + THRESHOLD -----------
async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global URL, THRESHOLD, LAST_SENT

    try:
        URL = context.args[0]
        THRESHOLD = int(context.args[1])
        LAST_SENT = None
        await update.message.reply_text("✅ Tracking updated!")
    except:
        await update.message.reply_text("Usage:\n/set <link> <threshold>")


# ----------- MANUAL COMMAND -----------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not URL:
        return await update.message.reply_text("⚠️ Use /set first")

    base_price, bank_discount = await get_price()

    if base_price:
        if base_price:
            if THRESHOLD and bank_discount >= THRESHOLD:
                msg = f"🔥 Deal Found!\n\n💻 Price: {base_price}\n💳 Bank Discount: ₹{bank_discount}\n\n🚀 Grab it fast!"
            else:
                msg = f"😕 No Big Savings Yet\n\n💻 Current Price: {base_price}\n💳 Bank Offer: ₹{bank_discount}\n\n⏳ Waiting for a better deal..."

            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("😕 Something went wrong...")


# ----------- AUTO CHECK -----------
async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    global LAST_SENT

    if not URL or not THRESHOLD:
        return

    base_price, bank_discount = await get_price()

    if base_price and bank_discount >= THRESHOLD and bank_discount != LAST_SENT:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"🔥 Deal Found!\n\n💻 Price: {base_price}\n💳 Bank Discount: ₹{bank_discount}\n\n🚀 Grab it fast!"
        )
        LAST_SENT = bank_discount


# ----------- APP START -----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("set", set_cmd))
app.add_handler(CommandHandler("price", price))

app.job_queue.run_repeating(auto_check, interval=300, first=10)

app.run_polling()