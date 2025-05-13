# customer_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters, \
    CallbackContext
from config import CUSTOMER_BOT_TOKEN, MAIN_ADMIN_ID, SECONDARY_ADMIN_ID
from database import *

# حالات المحادثة
VIEW_PRODUCTS, CREATE_ORDER, ORDER_QUANTITY, ORDER_NAME, ORDER_PHONE, ORDER_STATE, ORDER_MUNICIPALITY, ORDER_ADDRESS, ORDER_DELIVERY_TYPE = range(
    9)
CONTACT_US, SUGGESTION = range(2)


# رسالة الترحيب
def start(update: Update, context: CallbackContext):
    welcome_message = (
        "🎉 مرحبًا بكم في متجرنا الإلكتروني! نقدم لكم أفضل المنتجات بجودة عالية وأسعار تنافسية. "
        "تابعونا على صفحتنا على فيسبوك للحصول على العروض الحصرية: "
        "[صفحتنا](https://www.facebook.com/profile.php?id=100065654981659) 🚚 اطلب الآن واستمتع بخدمة توصيل سريعة!"
    )
    keyboard = [
        [InlineKeyboardButton("عرض المنتجات", callback_data="view_products")],
        [InlineKeyboardButton("إنشاء طلبية", callback_data="create_order")],
        [InlineKeyboardButton("اتصل بنا", callback_data="contact_us")],
        [InlineKeyboardButton("اقتراحات", callback_data="suggestion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")


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
    context.user_data['products'] = products
    context.user_data['current_product'] = 0
    show_product(update, context)


def show_product(update: Update, context: CallbackContext):
    query = update.callback_query
    products = context.user_data['products']
    current = context.user_data['current_product']
    if not products:
        query.message.reply_text("لا توجد منتجات في هذا القسم.")
        return
    prod = products[current]
    text = f"🛒 {prod[1]}\n📝 {prod[2]}\n💵 {prod[3]:.2f} د.ج\n📦 المخزون: {prod[6]}"
    keyboard = [
        [InlineKeyboardButton("⬅️ السابق", callback_data="prev_product"),
         InlineKeyboardButton("التالي ➡️", callback_data="next_product")],
        [InlineKeyboardButton("إضافة للسلة", callback_data=f"add_to_cart_{prod[0]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_photo(photo=prod[4], caption=text, reply_markup=reply_markup)


def navigate_products(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    products = context.user_data['products']
    current = context.user_data['current_product']
    if query.data == "prev_product":
        context.user_data['current_product'] = max(0, current - 1)
    elif query.data == "next_product":
        context.user_data['current_product'] = min(len(products) - 1, current + 1)
    show_product(update, context)


# إنشاء طلبية
def create_order(update: Update, context: CallbackContext):
    context.user_data['cart'] = []
    products = get_products()
    keyboard = [[InlineKeyboardButton(f"{prod[1]}", callback_data=f"order_{prod[0]}")] for prod in products]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("اختر المنتج:", reply_markup=reply_markup)
    return CREATE_ORDER


def order_select_product(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    product_id = int(query.data.split("_")[1])
    context.user_data['current_product_id'] = product_id
    query.message.reply_text("أدخل الكمية:")
    return ORDER_QUANTITY


def order_quantity(update: Update, context: CallbackContext):
    try:
        quantity = int(update.message.text)
        if quantity <= 0:
            raise ValueError
        product_id = context.user_data['current_product_id']
        conn = sqlite3.connect('/app/storage/ecommerce.db')
        c = conn.cursor()
        c.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        stock = c.fetchone()[0]
        conn.close()
        if stock < quantity:
            update.message.reply_text(f"الكمية المطلوبة غير متوفرة! المخزون الحالي: {stock}")
            return ORDER_QUANTITY
        context.user_data['cart'].append({'product_id': product_id, 'quantity': quantity})
        update.message.reply_text("هل تريد إضافة منتج آخر؟ (نعم/لا)")
        return ORDER_QUANTITY + 1
    except ValueError:
        update.message.reply_text("الكمية غير صحيحة! أدخل الكمية مرة أخرى:")
        return ORDER_QUANTITY


def order_add_more(update: Update, context: CallbackContext):
    if update.message.text.lower() == "نعم":
        products = get_products()
        keyboard = [[InlineKeyboardButton(f"{prod[1]}", callback_data=f"order_{prod[0]}")] for prod in products]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("اختر المنتج:", reply_markup=reply_markup)
        return CREATE_ORDER
    update.message.reply_text("أدخل اسمك الكامل:")
    return ORDER_NAME


def order_name(update: Update, context: CallbackContext):
    context.user_data['order'] = {'name': update.message.text}
    update.message.reply_text("أدخل رقم هاتفك:")
    return ORDER_PHONE


def order_phone(update: Update, context: CallbackContext):
    context.user_data['order']['phone'] = update.message.text
    update.message.reply_text("أدخل الولاية:")
    return ORDER_STATE


def order_state(update: Update, context: CallbackContext):
    context.user_data['order']['state'] = update.message.text
    update.message.reply_text("أدخل البلدية:")
    return ORDER_MUNICIPALITY


def order_municipality(update: Update, context: CallbackContext):
    context.user_data['order']['municipality'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("إلى المكتب", callback_data="delivery_office")],
        [InlineKeyboardButton("إلى المنزل", callback_data="delivery_home")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("اختر نوع التوصيل:", reply_markup=reply_markup)
    return ORDER_DELIVERY_TYPE


def order_delivery_type(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    delivery_type = "office" if query.data == "delivery_office" else "home"
    context.user_data['order']['delivery_type'] = delivery_type
    if delivery_type == "home":
        query.message.reply_text("أدخل العنوان:")
        return ORDER_ADDRESS
    return finalize_order(update, context)


def order_address(update: Update, context: CallbackContext):
    context.user_data['order']['address'] = update.message.text
    return finalize_order(update, context)


def finalize_order(update: Update, context: CallbackContext):
    order = context.user_data['order']
    cart = context.user_data['cart']
    customer_id = update.effective_user.id
    total_price = 0
    for item in cart:
        product = next((p for p in get_products() if p[0] == item['product_id']), None)
        if product:
            total_price += product[3] * item['quantity']
    delivery_fee = get_delivery_fee(order['state'], order['delivery_type'])
    total_price += delivery_fee
    address = order.get('address', '')
    order_id = add_order(customer_id, order['name'], order['phone'], order['state'],
                         order['municipality'], address, order['delivery_type'], total_price)
    for item in cart:
        add_order_item(order_id, item['product_id'], item['quantity'])
    text = f"🎉 شكرًا لطلبك!\nالسعر الإجمالي: {total_price:.2f} د.ج\nسنتواصل معك قريبًا."
    update.message.reply_text(text) if update.message else update.callback_query.message.reply_text(text)

    # إشعار للأدمن
    admin_text = f"🛒 طلبية جديدة #{order_id}\n👤 {order['name']}\n📞 {order['phone']}\n📍 {order['state']}, {order['municipality']}\n💵 {total_price:.2f} د.ج"
    context.bot.send_message(chat_id=MAIN_ADMIN_ID, text=admin_text)
    context.bot.send_message(chat_id=SECONDARY_ADMIN_ID, text=admin_text)

    context.user_data.clear()
    start(update, context)
    return ConversationHandler.END


# اتصل بنا
def contact_us(update: Update, context: CallbackContext):
    contacts = get_contact_info()
    keyboard = [[InlineKeyboardButton(contact[3], url=contact[2])] for contact in contacts]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text("📞 تواصل معنا:", reply_markup=reply_markup)


# اقتراحات
def suggestion(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text("أدخل اقتراحك:")
    return SUGGESTION


def suggestion_text(update: Update, context: CallbackContext):
    add_suggestion(update.effective_user.id, update.message.text)
    update.message.reply_text("شكرًا على اقتراحك!")
    start(update, context)
    return ConversationHandler.END


# إلغاء المحادثة
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("تم إلغاء العملية.")
    context.user_data.clear()
    start(update, context)
    return ConversationHandler.END


def main():
    updater = Updater(CUSTOMER_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(view_products, pattern="view_products"))
    dp.add_handler(CallbackQueryHandler(view_category_products, pattern="cat_"))
    dp.add_handler(CallbackQueryHandler(navigate_products, pattern="(prev_product|next_product)"))
    dp.add_handler(CallbackQueryHandler(order_select_product, pattern="add_to_cart_"))

    # محادثة إنشاء طلبية
    create_order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_order, pattern="create_order")],
        states={
            CREATE_ORDER: [CallbackQueryHandler(order_select_product, pattern="order_")],
            ORDER_QUANTITY: [MessageHandler(Filters.text & ~Filters.command, order_quantity)],
            ORDER_QUANTITY + 1: [MessageHandler(Filters.text & ~Filters.command, order_add_more)],
            ORDER_NAME: [MessageHandler(Filters.text & ~Filters.command, order_name)],
            ORDER_PHONE: [MessageHandler(Filters.text & ~Filters.command, order_phone)],
            ORDER_STATE: [MessageHandler(Filters.text & ~Filters.command, order_state)],
            ORDER_MUNICIPALITY: [MessageHandler(Filters.text & ~Filters.command, order_municipality)],
            ORDER_DELIVERY_TYPE: [CallbackQueryHandler(order_delivery_type, pattern="delivery_")],
            ORDER_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, order_address)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(create_order_conv)

    # اتصل بنا
    dp.add_handler(CallbackQueryHandler(contact_us, pattern="contact_us"))

    # اقتراحات
    suggestion_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(suggestion, pattern="suggestion")],
        states={
            SUGGESTION: [MessageHandler(Filters.text & ~Filters.command, suggestion_text)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(suggestion_conv)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
