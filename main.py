import asyncio, os
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN =   os.getenv("BOT_TOKEN")
CHAT_ID = "266428657"
THRESHOLD = 1800
LAST_SENT = None


def format_price(price):
    return int(price.replace("₹", "").replace(",", "").strip())

async def get_price():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        page = await browser.new_page()

        URL = "https://www.flipkart.com/lenovo-loq-2025-amd-ryzen-7-octa-core-24-gb-1-tb-ssd-windows-11-home-8-gb-graphics-nvidia-geforce-rtx-5050-15ahp10-gaming-laptop/p/itm2c8883c14f978"

        await page.goto(URL)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        await browser.close()

        tree = HTMLParser(html)

        try:
            base_price = tree.css_first('.v1zwn21l.v1zwn20._1psv1zeb9._1psv1ze0').text(strip=True)

            for node in tree.css("div"):
                if node.text(strip=True) == "Lowest price for you":
                    parent = node.parent
                    text = parent.text()

                    # count ₹ symbols
                    if text.count("₹") > 2:
                        prices = [x for x in text.split() if "₹" in x]
                        off_price = prices[-1]
                    else:
                        off_price = text.replace("Lowest price for you", "").strip()

                    bank_discount = format_price(base_price) - format_price(off_price)

                    return base_price, bank_discount

        except:
            pass

        return None, None


# ----------- MANUAL COMMAND -----------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base_price, bank_discount = await get_price()

    if base_price:
        await update.message.reply_text(
            f"Base Price: {base_price} | Bank Offer: {bank_discount}"
        )
    else:
        await update.message.reply_text("Oh! Price not found")


# ----------- AUTO CHECK (EVERY 5 MIN) -----------
async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    global LAST_SENT

    base_price, bank_discount = await get_price()

    if base_price and bank_discount >= THRESHOLD:
        if bank_discount != LAST_SENT:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🔥Deal Found!\n\n💻 Price: {base_price} \n💳 Bank Discount: ₹{bank_discount}\n\n🚀 Grab it fast!"
            )
            LAST_SENT = bank_discount


# ----------- APP START -----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("price", price))

# run every 5 minutes
app.job_queue.run_repeating(auto_check, interval=300, first=10)

app.run_polling()