"""Browser Tool Adapter: Content extraction, page analysis, source ranking, and citation generation."""

import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

def utc_date_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

class ExtractedPage(BaseModel):
    url: str
    title: str
    meta_description: str = ""
    headings: List[str] = Field(default_factory=list)
    clean_text: str
    markdown_content: str
    word_count: int
    reading_time_min: float
    retrieved_at: str = Field(default_factory=utc_date_str)

class RankedSource(BaseModel):
    url: str
    title: str
    relevance_score: float
    snippet: str
    citation: str

class BrowserToolAdapter:
    """Robust web content adapter for HTTP retrieval, extraction, ranking, and citation formatting."""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds
        self.user_agent = "Alpha-Cognitive-OS/2.0 (Automated Tool Layer)"

    def fetch_url(self, url: str) -> str:
        """Fetch raw HTML string from URL."""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            content_type = resp.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            raw_bytes = resp.read()
            return raw_bytes.decode(charset, errors="ignore")

    def extract_content(self, html: str, url: str = "") -> ExtractedPage:
        """Extract clean text, title, headings, and markdown from HTML."""
        # 1. Extract Title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else (url or "Untitled Page")
        title = re.sub(r"\s+", " ", title)

        # 2. Extract Meta Description
        meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
        meta_desc = meta_match.group(1).strip() if meta_match else ""

        # 3. Extract Headings
        headings = []
        for h_match in re.finditer(r"<h([1-3])[^>]*>(.*?)</h\1>", html, re.IGNORECASE | re.DOTALL):
            h_text = re.sub(r"<[^>]+>", "", h_match.group(2)).strip()
            if h_text:
                headings.append(f"H{h_match.group(1)}: {h_text}")

        # 4. Strip boilerplate tags
        cleaned = re.sub(r"<(script|style|nav|header|footer|aside|svg|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)

        # 5. Convert basic HTML to Markdown
        md = cleaned
        # Headers
        md = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", md, flags=re.IGNORECASE | re.DOTALL)
        # Paragraphs & Breaks
        md = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<br\s*/?>", "\n", md, flags=re.IGNORECASE)
        # Bold & Italic
        md = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", md, flags=re.IGNORECASE | re.DOTALL)
        md = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", md, flags=re.IGNORECASE | re.DOTALL)
        # Strip all remaining tags
        md = re.sub(r"<[^>]+>", " ", md)
        # Normalize whitespace
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in md.splitlines()]
        markdown_body = "\n".join([line for line in lines if line])

        clean_text = re.sub(r"[#*_`]", "", markdown_body)
        words = clean_text.split()
        word_count = len(words)
        reading_time = round(word_count / 200.0, 1)

        return ExtractedPage(
            url=url,
            title=title,
            meta_description=meta_desc,
            headings=headings[:10],
            clean_text=clean_text,
            markdown_content=markdown_body,
            word_count=word_count,
            reading_time_min=reading_time
        )

    def rank_sources(self, query: str, pages: List[ExtractedPage]) -> List[RankedSource]:
        """Rank pages by semantic relevance to query and generate citations."""
        query_words = set(re.findall(r"\w+", query.lower()))
        ranked: List[RankedSource] = []

        for p in pages:
            text_lower = p.clean_text.lower()
            title_lower = p.title.lower()

            matches = sum(1 for w in query_words if w in text_lower)
            title_matches = sum(1 for w in query_words if w in title_lower)

            score = 0.0
            if query_words:
                content_density = min(1.0, (matches / len(query_words)) * 0.6)
                title_density = min(1.0, (title_matches / len(query_words)) * 0.4)
                score = round(content_density + title_density, 3)

            # Generate snippet around best matching keyword
            snippet = p.meta_description
            if not snippet and p.clean_text:
                for qw in query_words:
                    idx = text_lower.find(qw)
                    if idx != -1:
                        start = max(0, idx - 60)
                        end = min(len(p.clean_text), idx + 140)
                        snippet = f"...{p.clean_text[start:end].strip()}..."
                        break
            if not snippet:
                snippet = p.clean_text[:200] + "..."

            citation = self.generate_citation(p.title, p.url, snippet, p.retrieved_at)
            ranked.append(RankedSource(
                url=p.url,
                title=p.title,
                relevance_score=score,
                snippet=snippet,
                citation=citation
            ))

        ranked.sort(key=lambda x: x.relevance_score, reverse=True)
        return ranked

    def generate_citation(self, title: str, url: str, snippet: str, date_str: str) -> str:
        """Produce standardized markdown citation format."""
        clean_title = title.replace("\n", " ").strip()
        return f"[{clean_title}]({url}) — \"{snippet.strip()}\" (Retrieved: {date_str})"

    def compare_pages(self, pages: List[ExtractedPage]) -> Dict[str, Any]:
        """Compare content across multiple pages."""
        if len(pages) < 2:
            return {"status": "error", "message": "At least 2 pages required for comparison."}

        summaries = []
        for p in pages:
            summaries.append({
                "url": p.url,
                "title": p.title,
                "word_count": p.word_count,
                "headings": p.headings[:5],
                "sample_text": p.clean_text[:300]
            })

        return {
            "sources_compared": len(pages),
            "sources": summaries,
            "comparison_note": f"Analyzed {len(pages)} sources for consensus and divergent points."
        }
