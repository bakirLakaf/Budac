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

import imghdr_compat as imghdr
from database import (
    init_db,
    add_category,
    get_categories,
    add_product,
    get_products,
    delete_product,
    update_product,
    get_orders,
    update_order_status,
    set_delivery_fee,
    set_contact_info,
    get_suggestions,
)

# متغيرات البيئة
TOKEN = os.getenv("ADMIN_BOT_TOKEN")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", 0))
SECONDARY_ADMIN_ID = int(os.getenv("SECONDARY_ADMIN_ID", 0))

# حالات المحادثة
CATEGORY_NAME, PRODUCT_NAME, PRODUCT_DESCRIPTION, PRODUCT_PRICE, PRODUCT_IMAGE, PRODUCT_CATEGORY, PRODUCT_STOCK = range(
    7)
DELIVERY_STATE, DELIVERY_OFFICE_FEE, DELIVERY_HOME_FEE = range(3)
CONTACT_TYPE, CONTACT_VALUE, CONTACT_DISPLAY_NAME = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in [MAIN_ADMIN_ID, SECONDARY_ADMIN_ID]:
        await update.message.reply_text("غير مصرح لك باستخدام هذا البوت!")
        return
    keyboard = [
        [InlineKeyboardButton("إضافة قسم", callback_data="add_category"),
         InlineKeyboardButton("إضافة منتج", callback_data="add_product")],
        [InlineKeyboardButton("حذف منتج", callback_data="delete_product"),
         InlineKeyboardButton("تعديل منتج", callback_data="edit_product")],
        [InlineKeyboardButton("عرض الطلبات", callback_data="view_orders"),
         InlineKeyboardButton("إعدادات التوصيل", callback_data="set_delivery")],
        [InlineKeyboardButton("معلومات الاتصال", callback_data="set_contact"),
         InlineKeyboardButton("عرض الاقتراحات", callback_data="view_suggestions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("مرحبًا، اختر إجراء:", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_category":
        await query.message.reply_text("أدخل اسم القسم:")
        return CATEGORY_NAME
    elif data == "add_product":
        await query.message.reply_text("أدخل اسم المنتج:")
        return PRODUCT_NAME
    elif data == "delete_product":
        categories = get_categories()
        if not categories:
            await query.message.reply_text("لا توجد أقسام!")
            return ConversationHandler.END
        keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر القسم:", reply_markup=reply_markup)
    elif data == "edit_product":
        categories = get_categories()
        if not categories:
            await query.message.reply_text("لا توجد أقسام!")
            return ConversationHandler.END
        keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"edit_cat_{cat[0]}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر القسم:", reply_markup=reply_markup)
    elif data == "view_orders":
        orders = get_orders()
        if not orders:
            await query.message.reply_text("لا توجد طلبات!")
            return
        for order in orders:
            keyboard = [
                [InlineKeyboardButton("قبول", callback_data=f"accept_{order[0]}"),
                 InlineKeyboardButton("رفض", callback_data=f"reject_{order[0]}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                f"طلب #{order[0]} من {order[2]}\nالحالة: {order[9]}\nالسعر: {order[8]}",
                reply_markup=reply_markup
            )
    elif data == "set_delivery":
        await query.message.reply_text("أدخل اسم الولاية:")
        return DELIVERY_STATE
    elif data == "set_contact":
        await query.message.reply_text("أدخل نوع الاتصال (مثل phone, whatsapp, facebook):")
        return CONTACT_TYPE
    elif data == "view_suggestions":
        suggestions = get_suggestions()
        if not suggestions:
            await query.message.reply_text("لا توجد اقتراحات!")
            return
        for suggestion in suggestions:
            await query.message.reply_text(f"اقتراح #{suggestion[0]} من {suggestion[1]}:\n{suggestion[2]}")


async def add_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    add_category(name)
    await update.message.reply_text(f"تم إضافة القسم: {name}")
    return ConversationHandler.END


async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product_name"] = update.message.text
    await update.message.reply_text("أدخل وصف المنتج:")
    return PRODUCT_DESCRIPTION


async def add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product_description"] = update.message.text
    await update.message.reply_text("أدخل سعر المنتج:")
    return PRODUCT_PRICE


async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["product_price"] = float(update.message.text)
        await update.message.reply_text("أرسل صورة المنتج:")
        return PRODUCT_IMAGE
    except ValueError:
        await update.message.reply_text("السعر غير صحيح! أدخل رقمًا:")
        return PRODUCT_PRICE


async def add_product_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("أرسل صورة فقط!")
        return PRODUCT_IMAGE
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_name = f"images/{photo.file_id}.jpg"
    os.makedirs("images", exist_ok=True)
    await file.download_to_drive(file_name)
    if imghdr.what(file_name) not in ["jpeg", "png"]:
        os.remove(file_name)
        await update.message.reply_text("الصورة غير مدعومة! أرسل صورة JPEG أو PNG:")
        return PRODUCT_IMAGE
    context.user_data["product_image"] = file_name
    categories = get_categories()
    if not categories:
        await update.message.reply_text("لا توجد أقسام! أضف قسمًا أولاً.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر القسم:", reply_markup=reply_markup)
    return PRODUCT_CATEGORY


async def add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split("_")[1])
    context.user_data["product_category"] = category_id
    await query.message.reply_text("أدخل كمية المخزون (افتراضي 10):")
    return PRODUCT_STOCK


async def add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stock = int(update.message.text) if update.message.text else 10
        add_product(
            context.user_data["product_name"],
            context.user_data["product_description"],
            context.user_data["product_price"],
            context.user_data["product_image"],
            context.user_data["product_category"],
            stock
        )
        await update.message.reply_text("تم إضافة المنتج!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("الكمية غير صحيحة! أدخل رقمًا:")
        return PRODUCT_STOCK


async def delete_product_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split("_")[1])
    products = get_products(category_id)
    if not products:
        await query.message.reply_text("لا توجد منتجات في هذا القسم!")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(prod[1], callback_data=f"del_{prod[0]}")] for prod in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("اختر المنتج للحذف:", reply_markup=reply_markup)


async def delete_product_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    delete_product(product_id)
    await query.message.reply_text("تم حذف المنتج!")


async def edit_product_select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split("_")[2])
    products = get_products(category_id)
    if not products:
        await query.message.reply_text("لا توجد منتجات في هذا القسم!")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(prod[1], callback_data=f"edit_{prod[0]}")] for prod in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("اختر المنتج للتعديل:", reply_markup=reply_markup)


async def edit_product_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    context.user_data["edit_product_id"] = product_id
    keyboard = [
        [InlineKeyboardButton("تعديل الاسم", callback_data="edit_name"),
         InlineKeyboardButton("تعديل الوصف", callback_data="edit_description")],
        [InlineKeyboardButton("تعديل السعر", callback_data="edit_price"),
         InlineKeyboardButton("تعديل الصورة", callback_data="edit_image")],
        [InlineKeyboardButton("تعديل القسم", callback_data="edit_category"),
         InlineKeyboardButton("تعديل المخزون", callback_data="edit_stock")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("اختر ما تريد تعديله:", reply_markup=reply_markup)


async def edit_product_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data
    context.user_data["edit_field"] = field
    if field == "edit_name":
        await query.message.reply_text("أدخل الاسم الجديد:")
    elif field == "edit_description":
        await query.message.reply_text("أدخل الوصف الجديد:")
    elif field == "edit_price":
        await query.message.reply_text("أدخل السعر الجديد:")
    elif field == "edit_image":
        await query.message.reply_text("أرسل الصورة الجديدة:")
    elif field == "edit_category":
        categories = get_categories()
        keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("اختر القسم الجديد:", reply_markup=reply_markup)
    elif field == "edit_stock":
        await query.message.reply_text("أدخل كمية المخزون الجديدة:")
    return field


async def edit_product_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data["edit_field"]
    product_id = context.user_data["edit_product_id"]
    if field == "edit_image":
        if not update.message.photo:
            await update.message.reply_text("أرسل صورة فقط!")
            return field
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_name = f"images/{photo.file_id}.jpg"
        os.makedirs("images", exist_ok=True)
        await file.download_to_drive(file_name)
        if imghdr.what(file_name) not in ["jpeg", "png"]:
            os.remove(file_name)
            await update.message.reply_text("الصورة غير مدعومة! أرسل صورة JPEG أو PNG:")
            return field
        update_product(product_id, image=file_name)
        await update.message.reply_text("تم تعديل الصورة!")
    else:
        value = update.message.text
        if field == "edit_name":
            update_product(product_id, name=value)
            await update.message.reply_text("تم تعديل الاسم!")
        elif field == "edit_description":
            update_product(product_id, description=value)
            await update.message.reply_text("تم تعديل الوصف!")
        elif field == "edit_price":
            try:
                price = float(value)
                update_product(product_id, price=price)
                await update.message.reply_text("تم تعديل السعر!")
            except ValueError:
                await update.message.reply_text("السعر غير صحيح! أدخل رقمًا:")
                return field
        elif field == "edit_stock":
            try:
                stock = int(value)
                update_product(product_id, stock=stock)
                await update.message.reply_text("تم تعديل المخزون!")
            except ValueError:
                await update.message.reply_text("الكمية غير صحيحة! أدخل رقمًا:")
                return field
    return ConversationHandler.END


async def edit_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split("_")[1])
    update_product(context.user_data["edit_product_id"], category_id=category_id)
    await query.message.reply_text("تم تعديل القسم!")
    return ConversationHandler.END


async def order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, order_id = query.data.split("_")
    status = "accepted" if action == "accept" else "rejected"
    update_order_status(int(order_id), status)
    await query.message.reply_text(f"تم تحديث حالة الطلب #{order_id} إلى: {status}")


async def set_delivery_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["delivery_state"] = update.message.text
    await update.message.reply_text("أدخل رسوم التوصيل للمكتب:")
    return DELIVERY_OFFICE_FEE


async def set_delivery_office_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["delivery_office_fee"] = float(update.message.text)
        await update.message.reply_text("أدخل رسوم التوصيل للمنزل:")
        return DELIVERY_HOME_FEE
    except ValueError:
        await update.message.reply_text("الرسوم غير صحيحة! أدخل رقمًا:")
        return DELIVERY_OFFICE_FEE


async def set_delivery_home_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        home_fee = float(update.message.text)
        set_delivery_fee(
            context.user_data["delivery_state"],
            context.user_data["delivery_office_fee"],
            home_fee
        )
        await update.message.reply_text("تم تحديث رسوم التوصيل!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("الرسوم غير صحيحة! أدخل رقمًا:")
        return DELIVERY_HOME_FEE


async def set_contact_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact_type"] = update.message.text
    await update.message.reply_text("أدخل قيمة الاتصال (مثل رابط أو رقم):")
    return CONTACT_VALUE


async def set_contact_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact_value"] = update.message.text
    await update.message.reply_text("أدخل اسم العرض (مثل 'واتساب - الرقم الأول'):")
    return CONTACT_DISPLAY_NAME


async def set_contact_display_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_contact_info(
        context.user_data["contact_type"],
        context.user_data["contact_value"],
        update.message.text
    )
    await update.message.reply_text("تم تحديث معلومات الاتصال!")
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
                CallbackQueryHandler(delete_product_select_category, pattern="^cat_"),
                CallbackQueryHandler(delete_product_confirm, pattern="^del_"),
                CallbackQueryHandler(edit_product_select_category, pattern="^edit_cat_"),
                CallbackQueryHandler(edit_product_select, pattern="^edit_"),
                CallbackQueryHandler(edit_product_field, pattern="^edit_"),
                CallbackQueryHandler(edit_product_category, pattern="^cat_"),
                CallbackQueryHandler(order_status, pattern="^(accept|reject)_"),
            ],
            states={
                CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_handler)],
                PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
                PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_description)],
                PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
                PRODUCT_IMAGE: [MessageHandler(filters.PHOTO, add_product_image)],
                PRODUCT_CATEGORY: [CallbackQueryHandler(add_product_category, pattern="^cat_")],
                PRODUCT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_stock)],
                DELIVERY_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delivery_state)],
                DELIVERY_OFFICE_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delivery_office_fee)],
                DELIVERY_HOME_FEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delivery_home_fee)],
                CONTACT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact_type)],
                CONTACT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact_value)],
                CONTACT_DISPLAY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_contact_display_name)],
                "edit_name": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
                "edit_description": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
                "edit_price": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
                "edit_image": [MessageHandler(filters.PHOTO, edit_product_value)],
                "edit_stock": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_product_value)],
            },
            fallbacks=[CommandHandler("cancel", cancel)]
        )
        application.add_handler(conv_handler)
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error in admin_bot: {e}")


if __name__ == "__main__":
    init_db()
    main()
