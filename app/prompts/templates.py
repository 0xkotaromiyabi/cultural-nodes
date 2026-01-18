"""Prompt templates for Cultural AI RAG system."""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate


# Main RAG prompt for cultural studies Q&A
CULTURAL_QA_TEMPLATE = """Anda adalah asisten AI yang ahli dalam bidang cultural studies, sastra, linguistik, dan ilmu bahasa. Anda memiliki pengetahuan mendalam tentang teori budaya, analisis sastra, struktur bahasa, dan fenomena linguistik.

Gunakan konteks berikut dari knowledge base untuk menjawab pertanyaan pengguna. Jika informasi tidak tersedia dalam konteks, sampaikan dengan jujur bahwa Anda tidak memiliki informasi tersebut dalam knowledge base, tetapi Anda dapat memberikan pengetahuan umum jika relevan.

Pedoman respons:
1. Berikan jawaban yang komprehensif dan akademis
2. Gunakan istilah teknis yang tepat dengan penjelasan jika diperlukan
3. Sertakan referensi ke sumber dalam konteks jika tersedia
4. Struktur jawaban dengan jelas menggunakan paragraf atau poin-poin

Konteks dari Knowledge Base:
{context}

Pertanyaan: {question}

Jawaban:"""

CULTURAL_QA_PROMPT = PromptTemplate(
    template=CULTURAL_QA_TEMPLATE,
    input_variables=["context", "question"]
)


# Prompt for summarizing cultural texts
SUMMARIZE_TEMPLATE = """Anda adalah ahli dalam meringkas teks akademis di bidang cultural studies, sastra, dan linguistik.

Ringkas teks berikut dengan mempertahankan konsep-konsep kunci, argumen utama, dan terminologi penting. Hasil ringkasan harus tetap informatif dan akademis.

Teks:
{text}

Ringkasan:"""

SUMMARIZE_PROMPT = PromptTemplate(
    template=SUMMARIZE_TEMPLATE,
    input_variables=["text"]
)


# Prompt for analyzing literary/cultural concepts
ANALYSIS_TEMPLATE = """Anda adalah ahli analisis dalam bidang cultural studies dan sastra.

Analisis konsep atau fenomena berikut dengan pendekatan kritis dan interdisipliner. Pertimbangkan aspek-aspek:
- Definisi dan konteks historis
- Perspektif teoretis yang relevan
- Implikasi sosial-budaya
- Hubungan dengan konsep lain

Konteks yang tersedia:
{context}

Konsep/Fenomena untuk dianalisis: {topic}

Analisis:"""

ANALYSIS_PROMPT = PromptTemplate(
    template=ANALYSIS_TEMPLATE,
    input_variables=["context", "topic"]
)


# Prompt for linguistic analysis
LINGUISTIC_TEMPLATE = """Anda adalah ahli linguistik dengan spesialisasi dalam analisis bahasa.

Analisis aspek linguistik berikut dengan mempertimbangkan:
- Struktur fonologis, morfologis, atau sintaksis (sesuai konteks)
- Aspek semantik dan pragmatik
- Variasi sosiolinguistik jika relevan
- Perbandingan lintas bahasa jika diperlukan

Konteks dari knowledge base:
{context}

Pertanyaan linguistik: {question}

Analisis:"""

LINGUISTIC_PROMPT = PromptTemplate(
    template=LINGUISTIC_TEMPLATE,
    input_variables=["context", "question"]
)


# System message for chat-based interactions
SYSTEM_MESSAGE = """Anda adalah Cultural AI, asisten yang ahli dalam:
- Cultural Studies: teori budaya, hegemoni, identitas, representasi
- Sastra: teori sastra, kritik sastra, analisis naratif
- Linguistik: fonologi, morfologi, sintaksis, semantik, pragmatik
- Ilmu Bahasa: sosiolinguistik, psikolinguistik, linguistik historis

Berikan jawaban yang akademis namun mudah dipahami. Gunakan referensi dari knowledge base yang tersedia."""


def get_qa_prompt() -> PromptTemplate:
    """Get the main Q&A prompt template."""
    return CULTURAL_QA_PROMPT


def get_summarize_prompt() -> PromptTemplate:
    """Get the summarization prompt template."""
    return SUMMARIZE_PROMPT


def get_analysis_prompt() -> PromptTemplate:
    """Get the analysis prompt template."""
    return ANALYSIS_PROMPT


def get_linguistic_prompt() -> PromptTemplate:
    """Get the linguistic analysis prompt template."""
    return LINGUISTIC_PROMPT
