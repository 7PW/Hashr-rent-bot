import re
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

RENT, BED_TYPE, BED_COUNT, BED_RENT = range(4)

def parse_number(input_str):
    input_str = input_str.strip().lower().replace(",", "").replace("،", "")
    input_str = re.sub(r'[^\dكk]', '', input_str)
    match = re.match(r'(\d+)([كk]?)', input_str)
    if match:
        number = int(match.group(1))
        if match.group(2) in ['ك', 'k']:
            number *= 1000
        return number
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🏠 أهلاً بك في حاسبة الاستثمار العقاري\n\n📌 أولاً: كم تدفع إيجار سنوي للبيت؟")
    return RENT

async def get_rent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    rent = parse_number(update.message.text)
    if rent is None:
        await update.message.reply_text("❌ الرجاء إدخال رقم الإيجار بشكل صحيح (مثال: 140000 أو 140k أو ١٤٠ك)")
        return RENT
    context.user_data["rent"] = rent
    await update.message.reply_text("🛏️ هل الأسرة من نوع مفرد (S) أو ثلاثي (T)؟ اكتب S أو T")
    return BED_TYPE

async def get_bed_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    if text not in ['s', 't']:
        await update.message.reply_text("❌ من فضلك اختر نوع السرير: S للمفرد أو T للثلاثي")
        return BED_TYPE
    context.user_data["bed_type"] = text
    await update.message.reply_text("🛏️ كم عدد الأسرة في البيت؟")
    return BED_COUNT

async def get_bed_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    beds = parse_number(update.message.text)
    if beds is None:
        await update.message.reply_text("❌ الرجاء إدخال رقم صحيح لعدد الأسرة")
        return BED_COUNT
    context.user_data["beds"] = beds
    await update.message.reply_text("💵 كم الإيجار الشهري لكل سرير؟")
    return BED_RENT

async def get_bed_rent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    rent_per_bed = parse_number(update.message.text)
    if rent_per_bed is None:
        await update.message.reply_text("❌ الرجاء إدخال قيمة إيجار السرير بشكل صحيح")
        return BED_RENT

    # Retrieve data
    yearly_rent = context.user_data["rent"]
    bed_type = context.user_data["bed_type"]
    beds = context.user_data["beds"]
    multiplier = 3 if bed_type == 't' else 1
    real_beds = beds * multiplier
    total_monthly_income = real_beds * rent_per_bed
    total_yearly_income = total_monthly_income * 12
    profit_percent = (total_yearly_income / yearly_rent) * 100

    # Format output
    formatted_month = f"{total_monthly_income:,}"
    formatted_year = f"{total_yearly_income:,}"
    formatted_rent = f"{yearly_rent:,}"
    formatted_percent = f"{profit_percent:.2f}"

    result = (
        f"📊 النتائج:\n"
        f"🔹 الإيجار السنوي للبيت: {formatted_rent} درهم\n"
        f"🔹 عدد الأسرة بعد التحويل: {real_beds}\n"
        f"🔹 الدخل الشهري الكلي: {formatted_month} درهم\n"
        f"🔹 الدخل السنوي الكلي: {formatted_year} درهم\n"
        f"🔹 نسبة الربح: {formatted_percent}%\n\n"
        f"🔁 احسب من جديد: /start"
    )
    await update.message.reply_text(result)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ تم الإلغاء. اكتب /start للبدء من جديد.")
    return ConversationHandler.END

if __name__ == '__main__':
    import os
    TOKEN = os.environ.get("BOT_TOKEN")  # تأكد أنك أضفت التوكن في Railway
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rent)],
            BED_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bed_type)],
            BED_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bed_count)],
            BED_RENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bed_rent)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()
