# مشروع Ceramic (Retail Suite - Frappe/ERPNext) — يعمل الآن ✅

## الوصول للنظام
- الرابط: http://localhost:8080
- تسجيل الدخول: `Administrator` / كلمة المرور `admin`
- بيانات تجريبية محمّلة: 3 معارض (Athar, الأساس, مجموعة الفيتوري)، شركة
  "Ceramic Showrooms Co"، مستخدمون تجريبيون لكل دور (owner@, accounts@,
  purchasing@, warehouse@, manager.vf@, ahmed@, mohamed@, ali@ — النطاق
  retailsuite.demo)، منتجات وعميلان وعرض سعر وفاتورتا مبيعات كمثال عملي.
- نقطة البيع: من Desk → Retail Suite (Workspace) → New Sale، أو مباشرة
  http://localhost:8080/app/ceramic-pos

## كيف تم التشغيل (البنية التقنية)
- Docker Desktop (WSL2 backend) على ويندوز — تم تفعيل ميزتي
  Windows Subsystem for Linux و Virtual Machine Platform (احتاج إعادة تشغيل
  للجهاز)، ثم تثبيت نواة WSL2 يدويًا لأن `wsl --install` فشل بسبب حجب شبكي
  لـ wsldownload.azureedge.net (تم تجاوزه بتنزيل wsl_update_x64.msi مباشرة
  وتثبيته عبر msiexec من نافذة Administrator).
- بيئة التشغيل: `frappe_docker` الرسمي (مستنسخ في `C:\docker-erpnext\frappe_docker`)
  باستخدام `pwd.yml` مع صور `frappe/erpnext:v15` (بدل v16 الافتراضية، لأن
  retail_suite بُني واختُبر على Frappe/ERPNext 15).
- تطبيقا `payments` (فرع version-15) و `retail_suite` (فرع
  claude/retail-suite-erpnext-architecture-ykrlfr من نفس مستودع Ceramic)
  تم جلبهما وتثبيتهما ومهاجرتهما على موقع باسم `frontend`.
- واجهة الـ POS (Vue3+TS) بُنيت عبر npm install / npm run build داخل
  apps/retail_suite/frontend، ثم bench build --app retail_suite.
- تم إصلاح بيانات تأسيسية كانت مفقودة لأن الموقع أُنشئ عبر
  `bench new-site --install-app erpnext` مباشرة بدل معالج الإعداد الكامل
  (بالضبط كما حذّر documentation/install-guide.md):
  - Warehouse Type "Transit" وبقية سجلات install_fixtures.install()
  - Price List "Standard Selling" / "Standard Buying" (عملة USD)
  - Global Defaults default_currency عُدّلت من INR إلى USD
  - Fiscal Year "2026" (2026-01-01 إلى 2026-12-31)

## أوامر مفيدة للمتابعة
كل الأوامر التالية تُشغَّل من PowerShell بعد `cd C:\docker-erpnext\frappe_docker`:

- إيقاف الحاويات: `docker compose -f pwd.yml stop`
- إعادة تشغيلها لاحقًا: `docker compose -f pwd.yml start`
- إيقاف وحذف الحاويات (البيانات تبقى في الـ volumes): `docker compose -f pwd.yml down`
- حذف كل شيء نهائيًا بما فيه البيانات: `docker compose -f pwd.yml down -v`
- الدخول لصدفة الحاوية الخلفية: `docker compose -f pwd.yml exec backend bash`
- مشاهدة السجلات: `docker compose -f pwd.yml logs -f backend`

## إصلاح إضافي: صفحة الـ POS كانت تظهر فارغة
السبب: `bench get-app`/`npm run build` نُفّذت داخل حاوية `backend` فقط عبر
`docker exec`، فتغيّراتها بقيت في الطبقة الخاصة بتلك الحاوية وحدها. حاوية
`frontend` (nginx) تخدم الملفات الثابتة (`/assets/...`) من نظام ملفاتها
الخاص، وهو منفصل عن `backend` (لا يشتركان إلا في مجلد `sites` كـ volume) —
فكان ملف `ceramic_pos.js` غير موجود لديها (404)، فتُحمَّل الصفحة والعنوان
فقط دون تشغيل تطبيق الـ POS.

الحل: أخذ صورة (`docker commit`) من حاوية backend بعد كل التثبيتات
والبناء، باسم `retail_suite_custom:v15`، وتحديث `pwd.yml` لتستخدمها كل
الخدمات (backend, frontend, queue-long, queue-short, scheduler, websocket)
بدل `frappe/erpnext:v15` الأصلية، ثم `docker compose -f pwd.yml up -d
--force-recreate <services>`. تم التأكد أن `/assets/retail_suite/frontend/ceramic_pos.js`
يُرجع 200 الآن من حاوية frontend.

**ملاحظة للمستقبل:** أي تعديل لاحق على كود retail_suite أو إعادة بناء
الواجهة يجب أن يُعاد بعده نفس الإجراء (commit + تحديث كل الحاويات)، أو
الأفضل الانتقال لبناء صورة مخصصة حقيقية عبر `docker-bake.hcl`/`apps.json`
الرسمية في frappe_docker إن استمر العمل على المشروع لفترة طويلة.

## تعديلات الجلسة الثانية (2026-08-11): 4 طلبات عمل

1. **تعطيل اشتراط تأكيد المورد افتراضيًا** - حقل جديد Retail Suite Settings
   > "Require Supplier Availability Confirmation" (افتراضيًا OFF). عند إيقافه:
   - المورد يُختار مباشرة على سطر الصنف (حقل جديد `custom_supplier` على
     Sales Invoice Item، ظاهر فقط عند Supply Source = Supplier).
   - الفاتورة، أمر توريد المورد (SDO)، وسند القبض تُصدر كلها دون الحاجة
     لسجل "Supplier Availability Confirmation" مسبق.
   - تفعيل الخيار مجددًا يعيد السلوك الأصلي (اشتراط تأكيد مؤكَّد).
   - الملفات: `retail_suite_settings.json/.py`, `fixtures/custom_field.json`,
     `services/sales_service.py`, `services/fulfillment_service.py`,
     `services/supplier_delivery_service.py`, `api/supplier_delivery.py`,
     `setup/demo_data.py`, و POS frontend (`AddToCartDialog.vue` +
     `api/supplier.ts` جديد + `cart.ts` + `CheckoutPanel.vue` + `types/index.ts`).
   - **ملاحظة مهمة غير منجزة:** ملفات الاختبار الأربعة
     (`tests/test_sales_service.py`, `test_fulfillment_service.py`,
     `test_supplier_delivery_service.py`, `test_workflow_integration.py`)
     لم تُحدَّث لتوقيعات الدوال الجديدة - ستفشل حتى تُعدَّل.

2. **السحب السالب لمخزن الشركة** - `Stock Settings.allow_negative_stock`
   فُعِّل مباشرة على الموقع الحي (إعداد ERPNext قياسي، وليس كود retail_suite).
   موثّق في `documentation/install-guide.md` تحت "Optional: allow delivering
   below zero stock".

3. **ترجمة التقارير** - أُضيفت ترجمات عربية لعناوين أعمدة كل التقارير الستة
   في `retail_suite/translations/ar.csv`، بالإضافة لنصوص واجهة POS الجديدة.

4. **إعادة تصميم جدول أصناف فاتورة المبيعات المطبوعة** - أُزيل عمودا
   "Boxes Quantity"/"Delivered Area (m²)"/"Price / m²" الثابتان، واستُبدلا
   بعمودين عامين "الكمية"/"السعر"؛ الوحدة تظهر الآن داخل قيمة الخلية نفسها
   (مثال: "3 م²" مع عدد الصناديق كملاحظة صغيرة، أو "45 / م²" للسعر) - أو
   الوحدة/السعر القياسيين لـ ERPNext لأي صنف لا يُحسب بالمتر المربع (قطعة/كيس...).
   الملف: `print_format/ceramic_sales_invoice/ceramic_sales_invoice.json`.

### مشكلة تقنية ظهرت وحُلّت: `sites/apps.txt` ناقص
حاوية `configurator` تكتب `sites/apps.txt` مرة واحدة فقط عند أول تشغيل
(قبل تثبيت `payments`/`retail_suite`)، فبقي الملف يحتوي `erpnext`/`frappe`
فقط. هذا كان يُسقط `bench build --app retail_suite` بخطأ
`TypeError: paths[0] ... undefined` (لأن esbuild يعتمد على هذا الملف
لتحديد مسارات التطبيقات). الحل: إعادة توليده يدويًا
(`ls -1 apps > sites/apps.txt`) ثم إعادة `bench build`.

### طريقة تطبيق أي تعديل كود لاحق على الحاوية
```
docker cp "c:\Fituri_Group\retail_suite\." frappe_docker-backend-1:/home/frappe/frappe-bench/apps/retail_suite/retail_suite/
docker cp "c:\Fituri_Group\frontend\." frappe_docker-backend-1:/home/frappe/frappe-bench/apps/retail_suite/frontend/
docker compose -f C:\docker-erpnext\frappe_docker\pwd.yml exec -u root backend bash -c "chown -R frappe:frappe /home/frappe/frappe-bench/apps/retail_suite"
docker compose -f C:\docker-erpnext\frappe_docker\pwd.yml exec backend bash -c "cd /home/frappe/frappe-bench && bench --site frontend migrate"
docker compose -f C:\docker-erpnext\frappe_docker\pwd.yml exec backend bash -c "cd /home/frappe/frappe-bench/apps/retail_suite/frontend && npm install && npm run build"
docker compose -f C:\docker-erpnext\frappe_docker\pwd.yml exec backend bash -c "cd /home/frappe/frappe-bench && bench build --app retail_suite"
docker commit frappe_docker-backend-1 retail_suite_custom:v15
docker compose -f C:\docker-erpnext\frappe_docker\pwd.yml up -d --force-recreate frontend queue-long queue-short scheduler websocket
```
(تذكير: أي تعديل على JSON لـ DocType/Print Format موجود مسبقًا يحتاج
بَذل تاريخ `modified` فيه ليأخذه `bench migrate` بالحسبان - راجع
install-guide.md.)

## تعديلات إضافية (نفس الجلسة): دعم الأصناف غير المحسوبة بالمتر المربع في الـ POS
اكتُشفت المشكلة عمليًا: إضافة صنف وحدته "Nos" (وليس مساحة/صندوق) للسلة كانت
تفشل بخطأ "does not have a valid Area Per Box configured" لأن حوار "أضف
للسلة" وواجهة الحساب كانا يفترضان دائمًا أن الصنف سيراميك.

الحل: تفرّع كامل حسب `custom_area_per_box` للصنف:
- Backend: `calculation_service.calculate_simple_row`/`apply_simple_row`/
  `is_area_based_item` (سعر × كمية عادية بوحدة قياس الصنف نفسها، عبر
  Item Price القياسي - بدون محرك تسعير مخصص) + endpoint جديد
  `api.calculation.preview_simple_row` + دعمها في `sales_service`/
  `quotation_service`/`api/catalog.py` (`stock_uom`, `price_per_uom`).
- Frontend: `AddToCartDialog.vue` يعرض حقل "الكمية" العادي (لا "المساحة
  المطلوبة") لهذه الأصناف، `ProductCard.vue`/`CartLineItem.vue` يعرضان
  السعر/الكمية بوحدتهما الفعلية، `types/index.ts` أضاف `isAreaBasedItem()`
  و`SimpleCalculationPreview`.

**ملاحظة تشغيلية:** أي صنف كهذا يحتاج **Item Price** مُعرَّفة في قائمة
الأسعار المستخدمة، بوحدة قياس الصنف نفسها (stock UOM، مثل Nos) - وإلا
يظهر "No price set" في البطاقة ("Test" في الاختبار الحي لم يكن له سعر
معرَّف، وهذا إعداد بيانات وليس خطأ في الكود).

### مشكلة متكررة حُلّت نهائيًا: apps.txt يُعاد ضبطه عند كل إعادة إنشاء
اكتُشف أن `docker compose up --force-recreate` يُعيد تشغيل حاوية
`configurator` كلما أُعيد إنشاء `backend` (لأنها تبعية `service_completed_
successfully`)، وكانت `configurator` لا تزال تستخدم الصورة الأصلية
`frappe/erpnext:v15` (بدون payments/retail_suite) فتكتب `sites/apps.txt`
ناقصًا من جديد. الحل الدائم: `configurator` أصبحت تستخدم
`retail_suite_custom:v15` مثل بقية الخدمات في `pwd.yml`.

## المصدر
- المستودع: https://github.com/Rgoodeffect/Ceramic.git
- الفرع المستخدم: `claude/retail-suite-erpnext-architecture-ykrlfr`
  (فرع `main` يحتوي فقط على README فارغ تقريبًا؛ الكود الفعلي على هذا الفرع)
- نسخة محلية من المستودع أيضًا موجودة في `c:\Fituri_Group` (نفس الفرع).
