import os
import logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

import database
import logo_generator

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# State flags
BRAND, NICHE, COLORS, STYLE, SLOGAN = range(5)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎨 Create Logo", callback_data="btn_create")],
        [InlineKeyboardButton("🏢 Business Logo", callback_data="style_Business"),
         InlineKeyboardButton("🎮 Gaming Logo", callback_data="style_Gaming")],
        [InlineKeyboardButton("💼 Brand Logo", callback_data="style_Brand"),
         InlineKeyboardButton("🎭 Mascot Logo", callback_data="style_Mascot")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="btn_settings"),
         InlineKeyboardButton("❓ Help", callback_data="btn_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 Welcome to *LogoCraft Bot*!\n"
        "Create stunning AI-generated logos for your business, startup, gaming team, or personal brand in minutes.\n\n"
        "✨ *Modern & professional designs*\n"
        "🎨 *Multiple logo styles available*\n"
        "🖼️ *High-quality commercial outputs*\n"
        "🚀 *Fast and easy to use*\n\n"
        "Select an option below or start by clicking 🎨 Create Logo."
    )
    if update.message:
        await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ *LogoCraft Manual Guide*\n\n"
        "1. Click **🎨 Create Logo**.\n"
        "2. Provide your Brand Name, Niche Category, and Colors when prompted.\n"
        "3. The bot will automatically compile an advanced visual design vector prompt for OpenAI engines.\n"
        "4. Your download file will be sent back instantly as a clean high-quality PNG graphic assets payload."
    )
    if update.message:
        await update.message.reply_text(help_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text)

async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    
    if query.data == "btn_create":
        await query.message.reply_text("🏢 Let's get started! What is your *Business or Brand name*?", parse_mode="Markdown")
        return BRAND
        
    elif query.data.startswith("style_"):
        chosen_style = query.data.split("_")[1]
        database.update_preference(uid, "style", chosen_style)
        await query.message.reply_text(f"✅ Preferred category default set to: *{chosen_style}*", parse_mode="Markdown")
        
    elif query.data == "btn_settings":
        prefs = database.get_preferences(uid)
        status = "Enabled (HD)" if prefs['premium_hd'] else "Standard (SD)"
        msg = f"⚙️ *Your Account Settings:*\n\nDefault Vector Style: `{prefs['style']}`\nRender Resolution Mode: `{status}`"
        await query.message.reply_text(msg, parse_mode="Markdown")
        
    elif query.data == "btn_help":
        await help_cmd(update, context)
        
    return ConversationHandler.END

async def get_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand_name'] = update.message.text
    await update.message.reply_text("📋 Great! What is your *Business niche or category*? (e.g. Technology, Fitness, Coffee Shop)", parse_mode="Markdown")
    return NICHE

async def get_niche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['niche'] = update.message.text
    await update.message.reply_text("🎨 Enter your *Preferred Color Palette* (e.g. Navy Blue and Gold, Pastel Pink, Minimalist Monochrome)", parse_mode="Markdown")
    return COLORS

async def get_colors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['colors'] = update.message.text
    styles = ["Minimalist", "Modern", "Luxury", "Vintage", "3D", "Flat", "Futuristic", "Elegant"]
    kb = [[InlineKeyboardButton(s, callback_data=f"pick_{s}")] for s in styles]
    await update.message.reply_text("✨ Select your desired *Logo Design Style* below:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    return STYLE

async def get_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['style'] = query.data.split("_")[1]
    await query.message.reply_text("✍️ Enter an *Optional Slogan/Tagline* (or type /skip to generate without text labels):", parse_mode="Markdown")
    return SLOGAN

async def process_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    slogan = "" if update.message.text == "/skip" else update.message.text
    
    brand = context.user_data.get('brand_name')
    niche = context.user_data.get('niche')
    colors = context.user_data.get('colors')
    style = context.user_data.get('style')
    
    status_msg = await update.message.reply_text("⏳ LogoCraft is engineering your prompt and generating your high-res design asset. Please hold on...")
    
    engineered_prompt = logo_generator.build_logo_prompt(brand, niche, colors, style, slogan)
    prefs = database.get_preferences(uid)
    
    url = await logo_generator.generate_logo(engineered_prompt, quality_hd=prefs['premium_hd'])
    
    if url:
        local_filename = f"logo_{uid}_{int(update.message.message_id)}.png"
        download_success = await logo_generator.download_image(url, local_filename)
        
        if download_success and os.path.exists(local_filename):
            with open(local_filename, "rb") as img:
                await update.message.reply_photo(photo=img, caption=f"✨ Here is your generated commercial logo vector for *{brand}*!", parse_mode="Markdown")
            database.log_generation(uid, brand, engineered_prompt, url)
            os.remove(local_filename)
        else:
            await update.message.reply_text("❌ Image processing error during down-stream compilation.")
    else:
        await update.message.reply_text("❌ API response block failure. Verify your credentials mapping balance limits.")
        
    await status_msg.delete()
    return ConversationHandler.END

def main():
    database.init_db()
    if not TOKEN:
        print("Fatal error: BOT_TOKEN missing from configuration profiles mapping context.")
        return
        
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_router, pattern="^btn_create")],
        states={
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_brand)],
            NICHE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_niche)],
            COLORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_colors)],
            STYLE: [CallbackQueryHandler(get_style, pattern="^pick_")],
            SLOGAN: [MessageHandler(filters.TEXT, process_logo)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(button_router, pattern="^(btn_|style_)"))
    application.add_handler(conv_handler)
    
    print("LogoCraft Core Engine Active...")
    application.run_polling()

if __name__ == '__main__':
    main()

