import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import TELEGRAM_BOT_TOKEN, CV_PDF_PATH
import database.db as db
from cv_parser.parser import CVParser
from automation.browser import ApplicationBrowser
from automation.filler import FormFiller

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Store ongoing browser sessions keyed by chat_id
# For a production multi-user bot, we'd key by user_id and handle multiple concurrent sessions.
# Since this is a personal bot, one session at a time is fine.
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to your 24/7 Internship Automation Bot!\n\n"
        "To apply for a job, just send me a message with the URL.\n"
        "Format: `https://job-url.com [Company] [Role]`\n\n"
        "If you don't provide Company and Role, I'll use 'Unknown'."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming job URLs."""
    text = update.message.text
    chat_id = update.message.chat_id

    # Simple parsing: assume first word is URL
    parts = text.split(maxsplit=2)
    url = parts[0]
    company = parts[1] if len(parts) > 1 else "Unknown"
    role = parts[2] if len(parts) > 2 else "Unknown"

    if not url.startswith("http"):
        await update.message.reply_text("❌ Please send a valid URL starting with http/https.")
        return

    # Check DB
    if db.has_applied(url, company, role):
        await update.message.reply_text(f"⚠️ You have already applied for {role} at {company}. Skipping.")
        return

    await update.message.reply_text(f"🚀 Starting application for {company} - {role}...\nRunning in headless mode...")

    # Start automation
    try:
        parser = CVParser(CV_PDF_PATH)
        cv_data = parser.parse()

        browser_mgr = ApplicationBrowser()
        await browser_mgr.start(headless=True)
        await browser_mgr.navigate(url)

        filler = FormFiller(browser_mgr, cv_data, CV_PDF_PATH)
        await filler.fill_generic_form()
        await filler.upload_cv()

        screenshot_path = f"logs/screenshot_{chat_id}.png"
        await filler.take_screenshot(screenshot_path)

        # Save session to wait for user button
        user_sessions[chat_id] = {
            "browser_mgr": browser_mgr,
            "filler": filler,
            "url": url,
            "company": company,
            "role": role
        }

        # Send screenshot with Inline Keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Submit", callback_data="submit"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        with open(screenshot_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo, 
                caption=f"📝 **Form Filled!**\n\nCompany: {company}\nRole: {role}\n\nPlease review the screenshot. Do you want to submit?", 
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

    except Exception as e:
        logger.error(f"Error during automation: {e}")
        await update.message.reply_text(f"❌ An error occurred: {e}")
        # Clean up if failed
        if chat_id in user_sessions:
            await user_sessions[chat_id]["browser_mgr"].stop()
            del user_sessions[chat_id]

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    action = query.data

    if chat_id not in user_sessions:
        await query.edit_message_caption(caption="⚠️ Session expired or not found.")
        return

    session = user_sessions[chat_id]
    browser_mgr = session["browser_mgr"]
    filler = session["filler"]
    url = session["url"]
    company = session["company"]
    role = session["role"]

    try:
        if action == "submit":
            await query.edit_message_caption(caption="⏳ Submitting application...")
            success = await filler.click_submit()
            if success:
                db.record_application(company, role, url, status="Submitted")
                await query.edit_message_caption(caption=f"✅ Application for {company} submitted successfully and saved to DB!")
            else:
                await query.edit_message_caption(caption=f"⚠️ Could not find submit button automatically. DB updated as manual review needed.")
                db.record_application(company, role, url, status="Manual Review")
                
        elif action == "cancel":
            await query.edit_message_caption(caption="❌ Application cancelled. Closing browser.")
            db.record_application(company, role, url, status="Cancelled")
            
    except Exception as e:
        logger.error(f"Error during callback action: {e}")
        await query.edit_message_caption(caption=f"❌ Error during action: {e}")
    finally:
        # Cleanup browser
        await browser_mgr.stop()
        del user_sessions[chat_id]

def main() -> None:
    """Run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in .env")
        return
        
    # Start a dummy HTTP server for Render's health checks
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")
            
    def start_dummy_server():
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), DummyHandler)
        server.serve_forever()
        
    threading.Thread(target=start_dummy_server, daemon=True).start()
    logger.info("Dummy HTTP server started.")
        
    db.init_db()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot is polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
