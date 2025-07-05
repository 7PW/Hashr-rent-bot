import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation states
RENT, PRICE = range(2)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "مرحباً بك في حاسبة حشر العقارية 🏡🧮\n\n"
        "سأساعدك تحسب ربحك من العقار خطوة بخطوة.\n\n"
        "أول شي، كم تدفع إيجار سنوي (بالدرهم)؟"
    )
    return RENT

# Parse numbers from various formats
def parse_number(input_str):
    input_str = input_str.strip().lower().replace(",", "").replace("،", "")
    input_str = re.sub(r'[^\dkك]', '', input_str)
    match = re.match(r'(\d+)([kك]?)', input_str)
    if match:
        num = int(match.group(1))
        if match.group(2) in ['k', 'ك']:
            num *= 1000
        return num
    return None

# Get rent input
async def get_rent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    rent = parse_number(update.message.text)
    if rent is None:
        await update.message.reply_text("🔢 من فضلك اكتب رقم الإيجار بشكل صحيح")
        return RENT
    context.user_data['rent'] = rent
    await update.message.reply_text("جميل، كم سعر العقار الإجمالي؟")
    return PRICE

# Get price input and calculate profit
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = parse_number(update.message.text)
    if price is None:
        await update.message.reply_text("🔢 من فضلك اكتب رقم السعر بشكل صحيح")
        return PRICE

    rent = context.user_data['rent']
    yearly_profit = rent
    monthly_profit = rent // 12
    profit_percent = (rent / price) * 100

    result = (
        f"💰 النتايج:\n"
        f"📍 قيمة العقار: {price:,} درهم\n"
        f"📈 صافي الربح السنوي: {yearly_profit:,} درهم\n"
        f"📆 الربح الشهري: {monthly_profit:,} درهم\n"
        f"📊 نسبة الربح: {profit_percent:.2f}%\n\n"
        f"🔁 احسب من جديد: /start"
    )
    await update.message.reply_text(result)
    return ConversationHandler.END

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم الإلغاء. أرسل /start للبدء من جديد")
    return ConversationHandler.END

# Main entry point
if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rent)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    print("✅ البوت يعمل الآن...")
    app.run_polling()
