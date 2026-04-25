import asyncio, os
from playwright.async_api import async_playwright
from selectolax.parser import HTMLParser
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


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

        if tree:
            for node in tree.css("div"):
                if node.text(strip=True) == "Lowest price for you":
                    parent = node.parent
                    return parent.text().replace("Lowest price for you", "")

        return "Oh! Price not found"
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = await get_price()
    await update.message.reply_text(p)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("price", price))
app.run_polling()

