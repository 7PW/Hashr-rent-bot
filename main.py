import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from flask import Flask
from threading import Thread

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

RENT, PRICE = range(2)

def parse_number(input_str):
    input_str = input_str.strip().lower()
    input_str = input_str.replace(",", "").replace("،", "")
    input_str = re.sub(r'[^\dkك]', '', input_str)
    match = re.match(r'(\d+)([kك]?)', input_str)
    if match:
        num = int(match.group(1))
        if match.group(2) in ['k', 'ك']:
            num *= 1000
        return num
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("مرحباً بك في حاسبة حشر العقارية 🏡🧮\n\nسأساعدك تحسب ربحك من العقار خطوة بخطوة.\n\nأول شي، كم تدفع إيجار سنوي (بالدرهم)؟")
    return RENT

async def get_rent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    rent = parse_number(update.message.text)
    if rent is None:
        await update.message.reply_text("🔢 من فضلك اكتب رقم الإيجار بشكل صحيح")
        return RENT
    context.user_data['rent'] = rent
    await update.message.reply_text("جميل، كم سعر العقار الإجمالي؟")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = parse_number(update.message.text)
    if price is None:
        await update.message.reply_text("🔢 من فضلك اكتب رقم السعر بشكل صحيح")
        return PRICE

    rent = context.user_data['rent']
    yearly_profit = rent
    monthly_profit = rent // 12
    profit_percent = (rent / price) * 100

    formatted_year = f"{yearly_profit:,}"
    formatted_month = f"{monthly_profit:,}"
    formatted_price = f"{price:,}"
    formatted_percent = f"{profit_percent:.2f}"

    result = (
        f"💰 النتايج:\n"
        f"📍 قيمة العقار: {formatted_price} درهم\n"
        f"📈 صافي الربح السنوي: {formatted_year} درهم\n"
        f"📆 الربح الشهري: {formatted_month} درهم\n"
        f"📊 نسبة الربح: {formatted_percent}%\n\n"
        f"🔁 احسب من جديد: /start"
    )
    await update.message.reply_text(result)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم الإلغاء. أرسل /start للبدء من جديد")
    return ConversationHandler.END

# Flask to keep alive
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    from threading import Thread
    Thread(target=run_flask).start()

    app = ApplicationBuilder().token("ضع_توكن_البوت_هنا").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rent)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("✅ البوت شغّال الآن ويستقبل الأوامر...")
    app.run_polling()
