# AI Match
## AI-Powered CV Screening and Job Matching System
## نظام تحليل السير الذاتية ومطابقتها بالوظائف بالذكاء الاصطناعي

English first. التوثيق العربي أدناه.

---

## English

### Project Overview

AI Match is a local application that compares CVs with job descriptions and explains detected skill gaps.

It combines semantic similarity, TF-IDF lexical similarity, and skill coverage to calculate match scores. Users can compare a CV with ten fictional demo jobs or enter their own job description.

Location, job-type, and field preferences influence ranking separately from the match score.

This repository contains source code for users to download and run on their computers. It is not a publicly hosted website.

### Features

- Local registration and login with salted scrypt password hashing.
- Text extraction from PDF, DOCX, and UTF-8 TXT files.
- Optional local CV storage, download, and deletion.
- Semantic matching with Sentence Transformers and FAISS.
- TF-IDF similarity and predefined skill detection.
- Explanations of matching skills and skills not detected.
- Preference-based ranking.
- Local analysis history and JSON export.
- Offline model loading after initial setup.

### Technology Stack

| Component | Technology |
| --- | --- |
| Language | Python |
| Interface | Streamlit |
| Embedding model | all-MiniLM-L6-v2 |
| Vector search | FAISS |
| Lexical similarity | scikit-learn |
| Database | SQLite |
| Document extraction | PyPDF2 and python-docx |

### Windows Setup

Python 3.12 was used during development.

Download or clone the repository, open its folder in PowerShell, and run:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

Download the public embedding model once:

    python prepare_model.py --download

This explicit setup step contacts Hugging Face. It downloads model files without reading or uploading CVs or the application database. Dependency installation also requires internet access.

If the model is already cached, skip the download.

Verify offline loading:

    python -c "from database.vector_agent import embed_text; print(embed_text('Python SQL').shape)"

Expected shape: (384,).

Start the application from the repository root:

    python -m streamlit run app.py

Open http://127.0.0.1:8501 in your browser.

### Usage

1. Create a local account and sign in.
2. Set optional preferences in Profile.
3. Upload a text-based English CV in Dashboard.
4. Choose Demo jobs or Paste a job description.
5. Select Analyze Match and review the results.
6. Open History to review previous analyses.

Saving the CV is optional. Successful analyses are saved locally.
Deleting a CV does not delete analysis history; delete that separately from History.

### Scoring

| Component | Weight |
| --- | ---: |
| Skill coverage | 60% |
| Semantic similarity | 25% |
| Lexical similarity | 15% |

Components use a 0–100 scale. Negative semantic similarity is clamped to zero.

If no recognised job skills are detected, the fallback uses 75% semantic similarity and 25% lexical similarity.

Preference bonuses: location +10, job type +8, field +12.

Ranking points = match score + preference bonuses.
Match scores range from 0 to 100. Ranking points can reach 130.
Preferences reorder results rather than strictly filtering jobs.

Weights and labels are heuristic. They are not hiring probabilities or verified measures of proficiency.

### Privacy and Limitations

- Runtime matching uses a locally cached model.
- The application workflow has no GitHub API integration, email sending, or live job scraping.
- Streamlit usage statistics are disabled.
- The server listens on 127.0.0.1.
- Local data is stored in runtime/ai_match_v2.db.
- Passwords are hashed; saved CVs and results are not encrypted at rest.
- Email addresses identify local accounts and are not verified.
- English is the intended language for semantic matching.
- Limited Arabic skill aliases do not provide full Arabic support.
- No OCR is included for scanned PDFs.
- Skill detection uses a fixed vocabulary and does not reliably interpret negation.
- Long inputs may be truncated by the embedding model.
- Skill mentions do not prove competence or experience.
- Demo jobs are fictional; manually entered jobs are not verified.
- This local prototype is not a hardened public multi-user service.

Keep real test documents in private_data/ or uploads/.
Do not commit CVs, databases, credentials, or secrets. Review staged files before pushing.

### Project Structure

| Path | Purpose |
| --- | --- |
| app.py | Interface and workflow |
| auth_db.py | Accounts, profiles, and saved CVs |
| agents/cv_agent.py | Text extraction and skills |
| agents/job_agent.py | Demo jobs and job text |
| agents/match_agent.py | Scoring and ranking |
| agents/recommendation_agent.py | Recommendation explanations |
| database/vector_agent.py | Offline embeddings and search |
| database/db.py | Database schema and history |
| data/sample_jobs.py | Fictional job data |
| prepare_model.py | Explicit initial model download |

### Academic Background

Based on the King Khalid University graduation project, AI-Powered CV Screening and Job Matching System.

Original team:
- Abdulaziz Mansour Al-Shahrani
- Ali Naji Ali Al-Harth
- Thamer Eid Mahdi Al-Hashish
- Faisal Al-Hudaithy
- Meshari Abdulrahman Al-Qahtani

Supervisor: Dr. Atef Al Massmoudi.

This revised local version is maintained by Thamer Eid Mahdi Al-Hashish.

---

## العربية

### فكرة المشروع

AI Match تطبيق محلي لمقارنة السير الذاتية بأوصاف الوظائف وشرح المهارات المشتركة والمهارات التي لم يكتشفها النظام في السيرة.

يجمع التطبيق بين التشابه الدلالي والتشابه اللفظي باستخدام TF-IDF وتغطية المهارات لحساب درجة المطابقة. يستطيع المستخدم المقارنة مع عشر وظائف تجريبية خيالية أو إدخال وصف وظيفة بنفسه.

تؤثر تفضيلات الموقع ونوع العمل والمجال في ترتيب النتائج بصورة مستقلة عن درجة المطابقة الأساسية.

يوفر المستودع الأكواد لتنزيل المشروع وتشغيله على جهاز المستخدم، ولا يمثل موقعًا منشورًا على استضافة عامة.

### المميزات

- إنشاء الحسابات وتسجيل الدخول محليًا.
- تجزئة كلمات المرور باستخدام scrypt وملح عشوائي.
- قراءة ملفات PDF وDOCX وTXT بترميز UTF-8.
- حفظ السيرة محليًا بصورة اختيارية وتنزيلها وحذفها.
- مطابقة دلالية باستخدام Sentence Transformers وFAISS.
- تشابه لفظي باستخدام TF-IDF واكتشاف المهارات من قائمة محددة.
- تفسير المهارات المشتركة والمهارات غير المكتشفة.
- ترتيب النتائج وفق التفضيلات.
- سجل تحليلات محلي وتصدير النتائج بصيغة JSON.
- تحميل النموذج محليًا بعد التجهيز الأولي.

### التقنيات المستخدمة

| المكوّن | التقنية |
| --- | --- |
| لغة البرمجة | Python |
| الواجهة | Streamlit |
| نموذج التمثيل الدلالي | all-MiniLM-L6-v2 |
| البحث بالمتجهات | FAISS |
| التشابه اللفظي | scikit-learn |
| قاعدة البيانات | SQLite |
| قراءة المستندات | PyPDF2 وpython-docx |

### التثبيت على ويندوز

استُخدم Python 3.12 أثناء التطوير.

نزّل المستودع أو استنسخه، ثم افتح مجلده في PowerShell ونفّذ:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

نزّل النموذج العام مرة واحدة:

    python prepare_model.py --download

تتصل خطوة التجهيز هذه بموقع Hugging Face لتنزيل النموذج، ولا تقرأ السير الذاتية أو قاعدة البيانات ولا ترفعهما. تثبيت المكتبات يحتاج إنترنت أيضًا.

إذا كان النموذج موجودًا مسبقًا، تجاوز خطوة التنزيل.

اختبر تحميله دون اتصال:

    python -c "from database.vector_agent import embed_text; print(embed_text('Python SQL').shape)"

الشكل المتوقع: (384,).

شغّل التطبيق من المجلد الرئيسي:

    python -m streamlit run app.py

افتح http://127.0.0.1:8501 في المتصفح.

### طريقة الاستخدام

1. أنشئ حسابًا محليًا وسجّل الدخول.
2. اضبط التفضيلات اختياريًا من Profile.
3. ارفع سيرة إنجليزية تحتوي على نص قابل للاستخراج في Dashboard.
4. اختر Demo jobs أو Paste a job description.
5. اضغط Analyze Match وراجع النتائج.
6. افتح History لعرض التحليلات السابقة.

حفظ ملف السيرة اختياري، وتُحفظ التحليلات الناجحة محليًا.
حذف السيرة لا يحذف سجل التحليل؛ يمكن حذف السجل بصورة منفصلة من History.

### حساب الدرجات

| المكوّن | الوزن |
| --- | ---: |
| تغطية المهارات | 60% |
| التشابه الدلالي | 25% |
| التشابه اللفظي | 15% |

تُستخدم المكونات على مقياس من صفر إلى 100، ويُعامل التشابه الدلالي السالب على أنه صفر.

عند عدم اكتشاف مهارات معروفة في الوظيفة، تستخدم المعادلة البديلة 75% للتشابه الدلالي و25% للتشابه اللفظي.

نقاط التفضيلات: الموقع 10، ونوع العمل 8، والمجال 12.

نقاط الترتيب = درجة المطابقة + نقاط التفضيلات.
درجة المطابقة من صفر إلى 100، وقد تصل نقاط الترتيب إلى 130.
التفضيلات تعيد ترتيب الوظائف ولا تستبعد الوظائف الأخرى تلقائيًا.

الأوزان والتصنيفات تقديرية، ولا تمثل احتمالات قبول أو مقاييس موثّقة للإتقان.

### الخصوصية والقيود

- تستخدم المطابقة نموذجًا مخزّنًا محليًا.
- مسار عمل التطبيق لا يربط GitHub API أو يرسل بريدًا أو يجلب وظائف من الإنترنت.
- إحصاءات استخدام Streamlit معطّلة.
- الخادم يستمع على العنوان المحلي 127.0.0.1.
- البيانات المحلية محفوظة داخل runtime/ai_match_v2.db.
- كلمات المرور مجزّأة، لكن السير والنتائج غير مشفّرة عند التخزين.
- البريد معرّف محلي للحساب ولا يجري التحقق منه.
- الإنجليزية هي اللغة المستهدفة للمطابقة الدلالية.
- بعض مرادفات المهارات العربية لا تعني دعم العربية بالكامل.
- لا يوجد OCR لملفات PDF المصوّرة.
- المهارات تُكتشف من قائمة ثابتة، ولا يُفسّر النفي بصورة موثوقة.
- قد يقتطع النموذج النصوص الطويلة.
- ذكر المهارة لا يثبت الإتقان أو الخبرة.
- الوظائف التجريبية خيالية، والأوصاف اليدوية غير متحقق منها.
- هذه نسخة محلية تجريبية وليست خدمة عامة مجهّزة لتعدد المستخدمين عبر الإنترنت.

ضع المستندات الحقيقية داخل private_data/ أو uploads/.
لا ترفع السير أو قواعد البيانات أو بيانات الدخول أو الأسرار، وراجع الملفات قبل رفعها.

### هيكل المشروع

| المسار | الوظيفة |
| --- | --- |
| app.py | الواجهة ومسار الاستخدام |
| auth_db.py | الحسابات والملفات الشخصية والسير المحفوظة |
| agents/cv_agent.py | استخراج النص والمهارات |
| agents/job_agent.py | الوظائف التجريبية ونص المطابقة |
| agents/match_agent.py | الدرجات والترتيب |
| agents/recommendation_agent.py | تفسير التوصيات |
| database/vector_agent.py | التمثيل الدلالي المحلي والبحث |
| database/db.py | الجداول وسجل التحليل |
| data/sample_jobs.py | بيانات الوظائف الخيالية |
| prepare_model.py | تنزيل النموذج في خطوة تجهيز منفصلة |

### الخلفية الأكاديمية

مبني على مشروع تخرج بجامعة الملك خالد بعنوان: نظام تحليل السير الذاتية ومطابقتها بالوظائف باستخدام الذكاء الاصطناعي.

الفريق الأصلي:
- عبدالعزيز منصور الشهراني
- علي ناجي علي آل حارث
- ثامر عيد مهدي الحشيش
- فيصل الحُديثي
- مشاري عبدالرحمن القحطاني

بإشراف الدكتور عاطف المسعودي.

يتولى ثامر عيد مهدي الحشيش صيانة هذه النسخة المحلية المطوّرة.