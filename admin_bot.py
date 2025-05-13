# admin_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, CallbackContext
from config import ADMIN_BOT_TOKEN, MAIN_ADMIN_ID, SECONDARY_ADMIN_ID
from database import *

# حالات المحادثة
ADD_PRODUCT, ADD_PRODUCT_NAME, ADD_PRODUCT_DESC, ADD_PRODUCT_PRICE, ADD_PRODUCT_IMAGE, ADD_PRODUCT_CATEGORY = range(6)
REMOVE_PRODUCT, EDIT_PRODUCT, EDIT_PRODUCT_FIELD = range(3)
SET_DELIVERY_FEE, SET_CONTACT_INFO, VIEW_ORDERS, VIEW_SUGGESTIONS = range(4)
ADD_CATEGORY = range(1)  # حالة لإضافة قسم

# التحقق من هوية الأدمن
def check_admin(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    if user_id not in [MAIN_ADMIN_ID, SECONDARY_ADMIN_ID]:
        update.message.reply_text("غير مصرح لك بالوصول إلى هذا البوت!")
        return False
    return True

# الأوامر الأساسية
def start(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return
    stats = f"📊 حالة البوت:\n"
    stats += f"- عدد الأقسام: {len(get_categories())}\n"
    stats += f"- عدد المنتجات: {len(get_products())}\n"
    stats += f"- عدد الطلبيات: {len(get_orders())}"
    keyboard = [
        [InlineKeyboardButton("عرض المنتجات", callback_data="view_products")],
        [InlineKeyboardButton("إضافة منتج", callback_data="add_product")],
        [InlineKeyboardButton("إزالة منتج", callback_data="remove_product")],
        [InlineKeyboardButton("تعديل منتج", callback_data="edit_product")],
        [InlineKeyboardButton("إضافة قسم", callback_data="add_category")],
        [InlineKeyboardButton("عرض الطلبيات", callback_data="view_orders")],
        [InlineKeyboardButton("تعديل أسعار التوصيل", callback_data="set_delivery_fee")],
        [InlineKeyboardButton("تعديل معلومات الاتصال", callback_data="set_contact_info")],
        [InlineKeyboardButton("عرض الاقتراحات", callback_data="view_suggestions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(stats, reply_markup=reply_markup)

# عرض المنتجات
def view_products(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    categories = get_categories()
    keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("اختر القسم:", reply_markup=reply_markup)

def view_category_products(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    category_id = int(query.data.split("_")[1])
    products = get_products(category_id)
    for prod in products:
        text = f"🛒 {prod[1]}\n📝 {prod[2]}\n💵 {prod[3]:.2f} د.ج\n📦 المخزون: {prod[6]}"
        query.message.reply_photo(photo=prod[4], caption=text)
    query.message.reply_text("تم عرض المنتجات.")

# إضافة منتج
def add_product(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    update.callback_query.message.reply_text("أدخل اسم المنتج:")
    return ADD_PRODUCT_NAME

def add_product_name(update: Update, context: CallbackContext):
    context.user_data['product'] = {'name': update.message.text}
    update.message.reply_text("أدخل وصف المنتج:")
    return ADD_PRODUCT_DESC

def add_product_desc(update: Update, context: CallbackContext):
    context.user_data['product']['description'] = update.message.text
    update.message.reply_text("أدخل سعر المنتج (مثال: 10.00):")
    return ADD_PRODUCT_PRICE

def add_product_price(update: Update, context: CallbackContext):
    try:
        price = float(update.message.text)
        context.user_data['product']['price'] = price
        update.message.reply_text("أرسل صورة المنتج:")
        return ADD_PRODUCT_IMAGE
    except ValueError:
        update.message.reply_text("السعر غير صحيح! أدخل السعر مرة أخرى (مثال: 10.00):")
        return ADD_PRODUCT_PRICE

def add_product_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1].get_file()
    context.user_data['product']['image'] = photo.file_id
    categories = get_categories()
    keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"add_cat_{cat[0]}")] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر القسم:", reply_markup=reply_markup)
    return ADD_PRODUCT_CATEGORY

def add_product_category(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    category_id = int(query.data.split("_")[2])
    product = context.user_data['product']
    add_product(product['name'], product['description'], product['price'], product['image'], category_id)
    query.message.reply_text("تم إضافة المنتج بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END

# إزالة منتج
def remove_product(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    products = get_products()
    keyboard = [[InlineKeyboardButton(f"{prod[1]}", callback_data=f"remove_{prod[0]}")] for prod in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("اختر المنتج للحذف:", reply_markup=reply_markup)
    return REMOVE_PRODUCT

def remove_product_confirm(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_id = int(query.data.split("_")[1])
    delete_product(product_id)
    query.message.reply_text("تم إزالة المنتج بنجاح!")
    return ConversationHandler.END

# تعديل منتج
def edit_product(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    products = get_products()
    keyboard = [[InlineKeyboardButton(f"{prod[1]}", callback_data=f"edit_{prod[0]}")] for prod in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("اختر المنتج للتعديل:", reply_markup=reply_markup)
    return EDIT_PRODUCT

def edit_product_select(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_id = int(query.data.split("_")[1])
    context.user_data['edit_product_id'] = product_id
    keyboard = [
        [InlineKeyboardButton("الاسم", callback_data="edit_name")],
        [InlineKeyboardButton("الوصف", callback_data="edit_desc")],
        [InlineKeyboardButton("السعر", callback_data="edit_price")],
        [InlineKeyboardButton("الصورة", callback_data="edit_image")],
        [InlineKeyboardButton("القسم", callback_data="edit_category")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("اختر الحقل للتعديل:", reply_markup=reply_markup)
    return EDIT_PRODUCT_FIELD

def edit_product_field(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    field = query.data
    context.user_data['edit_field'] = field
    if field == "edit_name":
        query.message.reply_text("أدخل الاسم الجديد:")
    elif field == "edit_desc":
        query.message.reply_text("أدخل الوصف الجديد:")
    elif field == "edit_price":
        query.message.reply_text("أدخل السعر الجديد (مثال: 10.00):")
    elif field == "edit_image":
        query.message.reply_text("أرسل الصورة الجديدة:")
    elif field == "edit_category":
        categories = get_categories()
        keyboard = [[InlineKeyboardButton(cat[1], callback_data=f"edit_cat_{cat[0]}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("اختر القسم الجديد:", reply_markup=reply_markup)
    return EDIT_PRODUCT_FIELD

def edit_product_value(update: Update, context: CallbackContext):
    product_id = context.user_data['edit_product_id']
    field = context.user_data['edit_field']
    if field in ["edit_name", "edit_desc"]:
        value = update.message.text
        update_product(product_id, name=value if field == "edit_name" else None, description=value if field == "edit_desc" else None)
    elif field == "edit_price":
        try:
            value = float(update.message.text)
            update_product(product_id, price=value)
        except ValueError:
            update.message.reply_text("السعر غير صحيح! أدخل السعر مرة أخرى:")
            return EDIT_PRODUCT_FIELD
    elif field == "edit_image":
        value = update.message.photo[-1].get_file().file_id
        update_product(product_id, image=value)
    update.message.reply_text("تم تعديل المنتج بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END

def edit_product_category(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_id = context.user_data['edit_product_id']
    category_id = int(query.data.split("_")[2])
    update_product(product_id, category_id=category_id)
    query.message.reply_text("تم تعديل القسم بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END

# إضافة قسم
def add_category(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    update.callback_query.message.reply_text("أدخل اسم القسم الجديد:")
    return ADD_CATEGORY

def add_category_name(update: Update, context: CallbackContext):
    category_name = update.message.text
    add_category(category_name)
    update.message.reply_text(f"تم إضافة القسم '{category_name}' بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END

# عرض الطلبيات
def view_orders(update: Update, context: CallbackContext):
    orders = get_orders()
    for order in orders:
        text = f"🛒 الطلبية #{order[0]}\n👤 {order[2]}\n📞 {order[3]}\n📍 {order[4]}, {order[5]}\n🏠 العنوان: {order[6]}\n🚚 نوع التوصيل: {order[7]}\n💵 {order[8]:.2f} د.ج\n📊 الحالة: {order[9]}"
        keyboard = [[InlineKeyboardButton(f"تغيير الحالة", callback_data=f"status_{order[0]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.reply_text(text, reply_markup=reply_markup)

def change_order_status(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    order_id = int(query.data.split("_")[1])
    keyboard = [
        [InlineKeyboardButton("جديد", callback_data=f"status_{order_id}_new")],
        [InlineKeyboardButton("قيد التوصيل", callback_data=f"status_{order_id}_shipping")],
        [InlineKeyboardButton("مكتمل", callback_data=f"status_{order_id}_completed")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text("اختر الحالة الجديدة:", reply_markup=reply_markup)

def set_order_status(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data.split("_")
    order_id, status = int(data[1]), data[2]
    update_order_status(order_id, status)
    query.message.reply_text(f"تم تحديث حالة الطلبية إلى: {status}")
    
    # إشعار للزبون
    conn = sqlite3.connect('/app/storage/ecommerce.db')
    c = conn.cursor()
    c.execute("SELECT customer_id FROM orders WHERE id = ?", (order_id,))
    customer_id = c.fetchone()[0]
    conn.close()
    context.bot.send_message(chat_id=customer_id, text=f"تم تحديث حالة طلبيتك #{order_id} إلى: {status}")

# تعديل أسعار التوصيل
def set_delivery_fee(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    update.callback_query.message.reply_text("أدخل الولاية:")
    return SET_DELIVERY_FEE

def set_delivery_fee_state(update: Update, context: CallbackContext):
    context.user_data['delivery_fee'] = {'state': update.message.text}
    update.message.reply_text("أدخل سعر التوصيل للمكتب (مثال: 5.00):")
    return SET_DELIVERY_FEE + 1

def set_delivery_fee_office(update: Update, context: CallbackContext):
    try:
        office_fee = float(update.message.text)
        context.user_data['delivery_fee']['office_fee'] = office_fee
        update.message.reply_text("أدخل سعر التوصيل للمنزل (مثال: 7.00):")
        return SET_DELIVERY_FEE + 2
    except ValueError:
        update.message.reply_text("السعر غير صحيح! أدخل سعر التوصيل للمكتب مرة أخرى:")
        return SET_DELIVERY_FEE + 1

def set_delivery_fee_home(update: Update, context: CallbackContext):
    try:
        home_fee = float(update.message.text)
        delivery_fee = context.user_data['delivery_fee']
        set_delivery_fee(delivery_fee['state'], delivery_fee['office_fee'], home_fee)
        update.message.reply_text("تم تحديث أسعار التوصيل بنجاح!")
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("السعر غير صحيح! أدخل سعر التوصيل للمنزل مرة أخرى:")
        return SET_DELIVERY_FEE + 2

# تعديل معلومات الاتصال
def set_contact_info(update: Update, context: CallbackContext):
    if not check_admin(update, context):
        return ConversationHandler.END
    update.callback_query.message.reply_text("أدخل نوع الاتصال (مثل: phone, facebook, whatsapp):")
    return SET_CONTACT_INFO

def set_contact_info_type(update: Update, context: CallbackContext):
    context.user_data['contact_info'] = {'type': update.message.text}
    update.message.reply_text("أدخل قيمة الاتصال (مثل رقم الهاتف أو الرابط):")
    return SET_CONTACT_INFO + 1

def set_contact_info_value(update: Update, context: CallbackContext):
    context.user_data['contact_info']['value'] = update.message.text
    update.message.reply_text("أدخل اسم العرض (مثل: فيسبوك, رقم الهاتف):")
    return SET_CONTACT_INFO + 2

def set_contact_info_display_name(update: Update, context: CallbackContext):
    contact_info = context.user_data['contact_info']
    set_contact_info(contact_info['type'], contact_info['value'], update.message.text)
    update.message.reply_text("تم تحديث معلومات الاتصال بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END

# عرض الاقتراحات
def view_suggestions(update: Update, context: CallbackContext):
    suggestions = get_suggestions()
    for sugg in suggestions:
        text = f"💡 الاقتراح #{sugg[0]}\n👤 المستخدم: {sugg[1]}\n📝 {sugg[2]}\n📅 {sugg[3]}"
        update.callback_query.message.reply_text(text)
    update.callback_query.message.reply_text("تم عرض جميع الاقتراحات.")

# إلغاء المحادثة
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("تم إلغاء العملية.")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    updater = Updater(ADMIN_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(view_products, pattern="view_products"))
    dp.add_handler(CallbackQueryHandler(view_category_products, pattern="cat_"))

    # محادثة إضافة منتج
    add_product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_product, pattern="add_product")],
        states={
            ADD_PRODUCT_NAME: [MessageHandler(Filters.text & ~Filters.command, add_product_name)],
            ADD_PRODUCT_DESC: [MessageHandler(Filters.text & ~Filters.command, add_product_desc)],
            ADD_PRODUCT_PRICE: [MessageHandler(Filters.text & ~Filters.command, add_product_price)],
            ADD_PRODUCT_IMAGE: [MessageHandler(Filters.photo, add_product_image)],
            ADD_PRODUCT_CATEGORY: [CallbackQueryHandler(add_product_category, pattern="add_cat_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(add_product_conv)

    # محادثة إزالة منتج
    remove_product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(remove_product, pattern="remove_product")],
        states={
            REMOVE_PRODUCT: [CallbackQueryHandler(remove_product_confirm, pattern="remove_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(remove_product_conv)

    # محادثة تعديل منتج
    edit_product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_product, pattern="edit_product")],
        states={
            EDIT_PRODUCT: [CallbackQueryHandler(edit_product_select, pattern="edit_")],
            EDIT_PRODUCT_FIELD: [
                CallbackQueryHandler(edit_product_field, pattern="edit_(name|desc|price|image|category)"),
                MessageHandler(Filters.text & ~Filters.command, edit_product_value),
                MessageHandler(Filters.photo, edit_product_value),
                CallbackQueryHandler(edit_product_category, pattern="edit_cat_")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(edit_product_conv)

    # محادثة إضافة قسم
    add_category_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_category, pattern="add_category")],
        states={
            ADD_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, add_category_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(add_category_conv)

    # عرض الطلبيات وتغيير الحالة
    dp.add_handler(CallbackQueryHandler(view_orders, pattern="view_orders"))
    dp.add_handler(CallbackQueryHandler(change_order_status, pattern="status_"))
    dp.add_handler(CallbackQueryHandler(set_order_status, pattern="status_.*_.*"))

    # محادثة تعديل أسعار التوصيل
    set_delivery_fee_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_delivery_fee, pattern="set_delivery_fee")],
        states={
            SET_DELIVERY_FEE: [MessageHandler(Filters.text & ~Filters.command, set_delivery_fee_state)],
            SET_DELIVERY_FEE + 1: [MessageHandler(Filters.text & ~Filters.command, set_delivery_fee_office)],
            SET_DELIVERY_FEE + 2: [MessageHandler(Filters.text & ~Filters.command, set_delivery_fee_home)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(set_delivery_fee_conv)

    # محادثة تعديل معلومات الاتصال
    set_contact_info_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_contact_info, pattern="set_contact_info")],
        states={
            SET_CONTACT_INFO: [MessageHandler(Filters.text & ~Filters.command, set_contact_info_type)],
            SET_CONTACT_INFO + 1: [MessageHandler(Filters.text & ~Filters.command, set_contact_info_value)],
            SET_CONTACT_INFO + 2: [MessageHandler(Filters.text & ~Filters.command, set_contact_info_display_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(set_contact_info_conv)

    # عرض الاقتراحات
    dp.add_handler(CallbackQueryHandler(view_suggestions, pattern="view_suggestions"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
