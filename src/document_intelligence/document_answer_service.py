"""Find local PDF/Word files and answer questions from their extracted text."""

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional
from xml.etree import ElementTree

from src.document_intelligence.file_search import FileSearchEngine
from src.intelligence.ollama_client import OllamaClient


@dataclass(frozen=True)
class DocumentEvidence:
    path: Path
    location: str
    text: str
    score: float


class DocumentAnswerService:
    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    MAX_DOCUMENTS_TO_SCAN = 5000
    MAX_EVIDENCE_ITEMS = 6
    MAX_CONTEXT_CHARS = 14000
    _STOP_WORDS = {
        "answer", "solve", "find", "search", "read", "from", "file", "document",
        "pdf", "docx", "word", "question", "please", "using", "my", "the", "a",
        "what", "is", "number", "no", "of", "in", "on", "to", "for", "and",
        "this",
        "উত্তর", "দাও", "দিয়ে", "থেকে", "খুঁজে", "খুঁজুন", "পড়ো", "পড়ো",
        "সমাধান", "করো", "ফাইল", "ডকুমেন্ট", "প্রশ্ন", "এই", "আমার", "এর",
        "টা", "টি", "কি", "কী",
    }

    @classmethod
    def answer(
        cls,
        command: str,
        roots: Optional[list[Path]] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> str:
        question = cls._extract_question(command)
        if not question:
            return "যে PDF বা Word ফাইল থেকে উত্তর চান, তার নাম বা বিষয় এবং প্রশ্নটি বলুন।"

        search_roots = roots or cls._requested_drive_roots(command) or FileSearchEngine.get_available_drives()
        if not search_roots:
            return "এই কম্পিউটারে কোনো accessible drive পাওয়া যায়নি।"

        explicit_path = cls._extract_document_path(command)
        if explicit_path and explicit_path.is_file():
            candidates = [explicit_path]
        else:
            candidates = cls._find_documents(command, search_roots)

        if not candidates:
            return "অনুমোদিত drive-গুলোতে মেলা PDF বা DOCX ফাইল পাওয়া যায়নি। ফাইলের নাম বা drive উল্লেখ করে আবার বলুন।"

        query_tokens = cls._tokens(question)
        file_hint = cls._extract_file_hint(command)
        evidence: list[DocumentEvidence] = []
        scanned = 0
        readable = 0
        scan_limit_reached = False

        for path in candidates:
            if scanned >= cls.MAX_DOCUMENTS_TO_SCAN:
                scan_limit_reached = True
                break
            scanned += 1
            if progress_cb and scanned % 25 == 0:
                progress_cb(f"{scanned}টি PDF/Word ফাইল পরীক্ষা করা হয়েছে...")

            try:
                sections = cls._extract_sections(path)
                readable += 1
            except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
                if progress_cb:
                    progress_cb(f"{path.name} পড়া যায়নি: {exc}")
                continue

            for location, text in sections:
                cleaned = text.strip()
                if not cleaned:
                    continue
                score = cls._relevance(query_tokens, cleaned)
                if (explicit_path and path.resolve() == explicit_path.resolve()) or (file_hint and path.name.lower() == file_hint.lower()):
                    score += 1.0
                if score > 0:
                    evidence.append(DocumentEvidence(path, location, cleaned[:3500], score))

        if scanned == 0:
            return "অনুমোদিত drive-গুলোতে মেলা PDF বা DOCX ফাইল পাওয়া যায়নি। ফাইলের নাম বা drive উল্লেখ করে আবার বলুন।"
        if readable == 0:
            return "PDF/Word ফাইল পাওয়া গেছে, কিন্তু সেগুলো পড়া যায়নি। ফাইলটি নষ্ট, password-protected, বা unsupported হতে পারে।"
        if not evidence:
            return "ফাইল পাওয়া গেছে, কিন্তু প্রশ্নের সঙ্গে মেলা পড়ার মতো text পাওয়া যায়নি। স্ক্যান করা PDF হলে OCR লাগতে পারে।"

        evidence.sort(key=lambda item: item.score, reverse=True)
        evidence = evidence[:cls.MAX_EVIDENCE_ITEMS]
        context_parts = [
            f"[Source: {item.path} | {item.location}]\n{item.text}"
            for item in evidence
        ]
        context = "\n\n".join(context_parts)[:cls.MAX_CONTEXT_CHARS]
        model = OllamaClient()
        answer = model.answer_from_context(question, context) if model.is_available() else None
        citations = ", ".join(
            f"{item.path.name} ({item.location})"
            for item in evidence[:3]
        )

        if answer:
            result = f"{answer.strip()}\n\nসূত্র: {citations}"
        else:
            excerpt = evidence[0]
            result = (
                "স্থানীয় AI model দিয়ে উত্তর তৈরি করা যায়নি। ডকুমেন্টে পাওয়া প্রাসঙ্গিক অংশ: "
                f"“{excerpt.text[:900]}”\nসূত্র: {excerpt.path} ({excerpt.location})"
            )
        if scan_limit_reached:
            result += "\nসতর্কতা: ৫০০০টি ফাইলের সীমায় scan থেমেছে; ফলাফল সম্পূর্ণ নাও হতে পারে।"
        return result

    @classmethod
    def _find_documents(cls, command: str, roots: list[Path]) -> Iterable[Path]:
        engine = FileSearchEngine()
        hint = cls._extract_file_hint(command)
        if hint:
            results = engine.search(
                hint,
                roots=roots,
                extensions=cls.ALLOWED_EXTENSIONS,
                max_results=20,
            )
            if results:
                return [result.path for result in results]

        return engine.iter_authorized_files(roots=roots, extensions=cls.ALLOWED_EXTENSIONS)

    @classmethod
    def _extract_sections(cls, path: Path) -> list[tuple[str, str]]:
        if path.suffix.lower() == ".pdf":
            import fitz

            with fitz.open(str(path)) as document:
                return [
                    (f"page {index + 1}", page.get_text("text") or "")
                    for index, page in enumerate(document)
                ]

        with zipfile.ZipFile(path) as archive:
            document_xml = ElementTree.fromstring(archive.read("word/document.xml"))
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = [
            "".join(node.itertext()).strip()
            for node in document_xml.findall(".//w:p", namespace)
        ]
        sections: list[tuple[str, str]] = []
        for start in range(0, len(paragraphs), 12):
            text = "\n".join(line for line in paragraphs[start:start + 12] if line)
            if text:
                end = min(start + 12, len(paragraphs))
                sections.append((f"paragraphs {start + 1}-{end}", text))
        return sections

    @classmethod
    def _extract_question(cls, command: str) -> str:
        question = command.strip()
        file_hint = cls._extract_file_hint(question)
        if file_hint:
            question = re.sub(re.escape(file_hint), " ", question, flags=re.IGNORECASE)
        question = re.sub(
            r"^(?:please\s+)?(?:find|search for|read|answer from|answer|solve from|open)\s+",
            "",
            question,
            flags=re.IGNORECASE,
        )
        question = re.sub(
            r"^(?:আমার\s+)?(?:পিডিএফ|pdf|word|ওয়ার্ড|ওয়ার্ড|ডকুমেন্ট|ফাইল)\s*",
            "",
            question,
            flags=re.IGNORECASE,
        )
        question = re.sub(r"\b(?:pdf|docx|word file|ডকুমেন্ট|ফাইল)\b", " ", question, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", question).strip(" .,:;")

    @staticmethod
    def _extract_document_path(command: str) -> Optional[Path]:
        match = re.search(
            r"(?:(?:[A-Za-z]:[\\/])[^\"'\r\n]+|[^\"'\r\n]*?)\.(?:pdf|docx)\b",
            command,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        raw_path = match.group(0).strip().strip("\"' .,")
        candidate = Path(raw_path)
        return candidate if candidate.is_absolute() else None

    @staticmethod
    def _extract_file_hint(command: str) -> str:
        match = re.search(r"([\w\u0980-\u09ff ._-]+\.(?:pdf|docx))\b", command, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _requested_drive_roots(command: str) -> list[Path]:
        match = re.search(
            r"\b([A-Za-z])\s*(?:drive|ড্রাইভ(?:ে|ের)?)\b",
            command,
            flags=re.IGNORECASE,
        )
        if not match:
            return []
        root = Path(f"{match.group(1).upper()}:\\")
        return [root] if root.exists() else []

    @classmethod
    def _tokens(cls, text: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+|[\u0980-\u09ff]+", text.lower())
        return {
            word for word in words
            if (len(word) > 1 or word.isdigit()) and word not in cls._STOP_WORDS
        }

    @staticmethod
    def _relevance(query_tokens: set[str], text: str) -> float:
        if not query_tokens:
            return 0.0
        document_tokens = set(re.findall(r"[a-z0-9]+|[\u0980-\u09ff]+", text.lower()))
        return len(query_tokens & document_tokens) / len(query_tokens)
