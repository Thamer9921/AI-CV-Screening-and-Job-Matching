import re
from io import BytesIO

from PyPDF2 import PdfReader
from docx import Document


SKILL_ALIASES = {
    "python": ["python", "بايثون"],
    "java": ["java", "جافا"],
    "javascript": ["javascript", "java script"],
    "typescript": ["typescript"],
    "sql": ["sql"],
    "git": ["git"],
    "linux": ["linux", "لينكس"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "react": ["react", "reactjs", "react.js"],
    "rest api": ["rest api", "restful api", "rest apis"],
    "api": ["api", "apis"],
    "artificial intelligence": ["artificial intelligence", "ai", "ذكاء اصطناعي", "الذكاء الاصطناعي"],
    "machine learning": ["machine learning", "ml", "تعلم الآلة"],
    "deep learning": ["deep learning", "التعلم العميق"],
    "nlp": ["nlp", "natural language processing", "معالجة اللغة الطبيعية"],
    "data analysis": ["data analysis", "data analytics", "تحليل البيانات"],
    "computer science": ["computer science", "علوم الحاسب", "علوم الحاسوب"],
    "programming": ["programming", "برمجة", "البرمجة"],
    "oop": ["oop", "object oriented programming", "object-oriented programming"],
    "data structures": ["data structures", "هياكل البيانات"],
    "algorithms": ["algorithms", "خوارزميات", "الخوارزميات"],
    "networking": ["networking", "computer networks", "شبكات الحاسب"],
    "network security": ["network security", "أمن الشبكات"],
    "cybersecurity": ["cybersecurity", "cyber security", "الأمن السيبراني"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "power bi": ["power bi", "powerbi"],
    "microsoft office": ["microsoft office", "ms office"],
    "excel": ["excel", "microsoft excel"],
    "word": ["microsoft word", "ms word"],
    "powerpoint": ["powerpoint", "power point"],
    "teamwork": ["teamwork", "team work", "العمل الجماعي"],
    "communication": ["communication", "مهارات التواصل"],
    "problem solving": ["problem solving", "problem-solving", "حل المشكلات"],
    "english": ["english", "الإنجليزية"],
    "arabic": ["arabic", "العربية"],
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def extract_text(filename, file_bytes):
    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("The maximum CV file size is 10 MB.")

    name = filename.lower()

    try:
        if name.endswith(".pdf"):
            reader = PdfReader(BytesIO(file_bytes))

            if reader.is_encrypted and not reader.decrypt(""):
                raise ValueError("Upload an unprotected PDF.")

            text = "\n".join(page.extract_text() or "" for page in reader.pages)

        elif name.endswith(".docx"):
            doc = Document(BytesIO(file_bytes))
            parts = [p.text for p in doc.paragraphs]

            for table in doc.tables:
                for row in table.rows:
                    parts.append(" ".join(cell.text for cell in row.cells))

            text = "\n".join(parts)

        elif name.endswith(".txt"):
            text = file_bytes.decode("utf-8-sig")

        else:
            raise ValueError("Supported formats: PDF, DOCX, TXT.")

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Could not read the file. Use a valid PDF, DOCX, or UTF-8 TXT."
        ) from exc

    text = text.strip()

    if not text:
        raise ValueError(
            "No readable text found. Scanned PDFs need OCR; "
            "upload a text-based PDF, DOCX, or TXT."
        )

    return text


def clean_text(text):
    text = text.casefold()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[_\-–—/]", " ", text)
    text = re.sub(r"[^\w\s+#.]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def extract_skills(text):
    cleaned = clean_text(text)
    found = []

    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = r"(?<!\w)" + re.escape(clean_text(alias)) + r"(?!\w)"
            if re.search(pattern, cleaned):
                found.append(skill)
                break

    return sorted(found)


def analyze_cv(filename, file_bytes):
    raw_text = extract_text(filename, file_bytes)
    return {
        "text": raw_text,
        "skills": extract_skills(raw_text),
    }