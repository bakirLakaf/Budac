# Ecommerce Bot

متجر إلكتروني يعمل على تلغرام، يتكون من بوتين:
- **بوت الأدمن**: لإدارة المنتجات، الأقسام، الطلبيات، أسعار التوصيل، ومعلومات الاتصال.
- **بوت الزبائن**: لعرض المنتجات، إنشاء الطلبيات، التواصل، وإرسال الاقتراحات.

## الميزات
- إدارة الأقسام والمنتجات (إضافة، تعديل، إزالة).
- إنشاء طلبيات مع دعم التوصيل للمكتب أو المنزل.
- إدارة المخزون (التحقق من الكميات قبل الطلب).
- إشعارات للأدمن عند استلام طلبية وللزبون عند تغيير حالة الطلبية.
- معلومات اتصال (فيسبوك، أرقام هاتف، واتساب).
- دعم النشر على Railway مع قاعدة بيانات SQLite.

## متطلبات النشر
1. حساب على [Railway](https://railway.app).
2. حساب على GitHub لإنشاء مستودع.
3. توكنات بوت الأدمن وبوت الزبائن من BotFather.
4. Python 3.7+.

## خطوات النشر
1. **إعداد المستودع**:
 - أنشئ مستودعًا على GitHub.
 - ارفع الملفات (`config.py`, `database.py`, `admin_bot.py`, `customer_bot.py`, `requirements.txt`, `Procfile`).

2. **إعداد Railway**:
 - سجّل في Railway وربط حساب GitHub.
 - أنشئ مشروعًا جديدًا واختر المستودع.
 - أضف خدمتين:
 - `admin`: تشغل `python admin_bot.py`.
 - `customer`: تشغل `python customer_bot.py`.
 - أضف وحدة تخزين (Volume) بمسار `/app/storage` وربطها بالخدمتين.
 - أضف متغيرات البيئة:
 - `ADMIN_BOT_TOKEN`
 - `CUSTOMER_BOT_TOKEN`
 - `MAIN_ADMIN_ID`
 - `SECONDARY_ADMIN_ID`

3. **النشر**:
 - اضغط على "Deploy" لكل خدمة.
 - تحقق من السجلات للتأكد من التشغيل.

4. **الاختبار**:
 - ابدأ بوت الأدمن بـ `/start` (للأدمن الرئيسي والفرعي).
 - ابدأ بوت الزبائن واختبر عرض المنتجات، إنشاء الطلبيات، ومعلومات الاتصال.

## ملاحظات
- تأكد من إعداد وحدة التخزين لتجنب فقدان قاعدة البيانات.
- احتفظ بنسخة احتياطية من `ecommerce.db`.
- لإضافة ميزات جديدة، راجع المطور.

## المطور
تم تطوير هذا المشروع بمساعدة Grok من xAI.
