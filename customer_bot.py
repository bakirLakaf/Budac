import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (

    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from tornado.web import Application

from database import (
    get_categories,
    get_products,
    add_order,
    add_order_item,
    get_delivery_fee,
    get_contact_info,
    add_suggestion,
)

# متغيرات البيئة
TOKEN = os.getenv("CUSTOMER_BOT_TOKEN")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", 0))
SECONDARY_ADMIN_ID = int(os.getenv("SECONDARY_ADMIN_ID", 0))

# حالات المحادثة
SELECT_CATEGORY, SELECT_PRODUCT, SELECT_QUANTITY, CUSTOMER_NAME, CUSTOMER_PHONE, CUSTOMER_STATE, CUSTOMER_MUNICIPALITY, CUSTOMER_ADDRESS, DELIVERY_TYPE, SUGGESTION_TEXT = range(
    10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    if not categories:
        await update.message.reply_text("لا توجد أقسام متاحة حاليًا!")
        return
    keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories]
    keyboard.append([InlineKeyboardButton("معلومات الاتصال", callback_data="contact_info")])
    keyboard.append([InlineKeyboardButton("إرسال اقتراح", callback_data="send_suggestion")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا! اختر قسمًا أو إجراءً:", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        category_id = int(data.split("_")[1])
        context.user_data["category_id"] = category_id
        products = get_products(category_id)
        if not products:
            await query.message.reply_text("لا توجد منتجات في هذا القسم!")
            return
        keyboard = [[InlineKeyboardButton(prod[1], callback_data=f"prod_{prod[0]}")] for prod in products]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر المنتج:", reply_markup=reply_markup)
        return SELECT_PRODUCT
    elif data == "contact_info":
        contacts = get_contact_info()
        if not contacts:
            await query.message.reply_text("لا توجد معلومات اتصال متاحة!")
            return
        message = "معلومات الاتصال:\n"
        for contact in contacts:
            message += f"- {contact[3]}: {contact[2]}\n"
        await query.message.reply_text(message)
    elif data == "send_suggestion":
        await query.message.reply_text("أدخل اقتراحك:")
        return SUGGESTION_TEXT


async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    context.user_data["product_id"] = product_id
    product = next((p for p in get_products(context.user_data["category_id"]) if p[0] == product_id), None)
    if not product:
        await query.message.reply_text("المنتج غير موجود!")
        return ConversationHandler.END
    await query.message.reply_photo(
        photo=open(product[4], "rb"),
        caption=f"{product[1]}\n{product[2]}\nالسعر: {product[3]} د.ج\nالمخزون: {product[6]}"
    )
    await query.message.reply_text("أدخل الكمية المطلوبة:")
    return SELECT_QUANTITY


async def select_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            await update.message.reply_text("الكمية يجب أن تكون أكبر من صفر!")
            return SELECT_QUANTITY
        context.user_data["quantity"] = quantity
        await update.message.reply_text("أدخل اسمك:")
        return CUSTOMER_NAME
    except ValueError:
        await update.message.reply_text("الكمية غير صحيحة! أدخل رقمًا:")
        return SELECT_QUANTITY


async def customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["customer_name"] = update.message.text
    await update.message.reply_text("أدخل رقم هاتفك:")
    return CUSTOMER_PHONE


async def customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["customer_phone"] = update.message.text
    await update.message.reply_text("أدخل اسم الولاية:")
    return CUSTOMER_STATE


async def customer_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["customer_state"] = update.message.text
    await update.message.reply_text("أدخل اسم البلدية:")
    return CUSTOMER_MUNICIPALITY


async def customer_municipality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["customer_municipality"] = update.message.text
    await update.message.reply_text("أدخل عنوانك:")
    return CUSTOMER_ADDRESS


async def customer_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["customer_address"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("توصيل للمكتب", callback_data="office"),
         InlineKeyboardButton("توصيل للمنزل", callback_data="home")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر نوع التوصيل:", reply_markup=reply_markup)
    return DELIVERY_TYPE


async def delivery_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    delivery_type = query.data
    context.user_data["delivery_type"] = delivery_type
    product_id = context.user_data["product_id"]
    quantity = context.user_data["quantity"]
    state = context.user_data["customer_state"]
    product = next((p for p in get_products() if p[0] == product_id), None)
    if not product:
        await query.message.reply_text("المنتج غير موجود!")
        return ConversationHandler.END
    total_price = product[3] * quantity
    delivery_fee = get_delivery_fee(state, delivery_type)
    total_price += delivery_fee
    order_id = add_order(
        update.effective_user.id,
        context.user_data["customer_name"],
        context.user_data["customer_phone"],
        state,
        context.user_data["customer_municipality"],
        context.user_data["customer_address"],
        delivery_type,
        total_price
    )
    add_order_item(order_id, product_id, quantity)
    await query.message.reply_text(
        f"تم إنشاء الطلب #{order_id}!\nالإجمالي: {total_price} د.ج (يشمل رسوم التوصيل: {delivery_fee} د.ج)"
    )
    for admin_id in [MAIN_ADMIN_ID, SECONDARY_ADMIN_ID]:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"طلب جديد #{order_id} من {context.user_data['customer_name']}\nالإجمالي: {total_price} د.ج"
        )
    return ConversationHandler.END


async def send_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    add_suggestion(update.effective_user.id, text)
    await update.message.reply_text("تم إرسال اقتراحك! شكرًا!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END


def main():
    try:
        application = Application.builder().token(TOKEN).build()
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                CallbackQueryHandler(button_callback),
                CallbackQueryHandler(select_product, pattern="^prod_"),
                CallbackQueryHandler(delivery_type, pattern="^(office|home)$"),
            ],
            states={
                SELECT_PRODUCT: [CallbackQueryHandler(select_product, pattern="^prod_")],
                SELECT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_quantity)],
                CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name)],
                CUSTOMER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_phone)],
                CUSTOMER_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_state)],
                CUSTOMER_MUNICIPALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_municipality)],
                CUSTOMER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_address)],
                DELIVERY_TYPE: [CallbackQueryHandler(delivery_type, pattern="^(office|home)$")],
                SUGGESTION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_suggestion)],
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        application.add_handler(conv_handler)
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error in customer_bot: {e}")


if __name__ == "__main__":
    main()
