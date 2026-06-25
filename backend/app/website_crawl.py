import html
import ipaddress
import json
import os
import re
import socket
import ssl
from urllib import error, request
from urllib.parse import urlparse
from zoneinfo import available_timezones

from backend.app.contracts import json_loads


USER_AGENT = "LocalPilotBot/1.0 (+https://localpilot.ai)"
FETCH_TIMEOUT_SECONDS = 12
MAX_FETCH_BYTES = 2 * 1024 * 1024
MAX_LLM_CHARS = 32000
MINIMAX_CHAT_COMPLETIONS_URL = "https://api.minimax.io/v1/chat/completions"
PROFILE_FIELDS = (
    "name",
    "description",
    "industry",
    "logo_url",
    "primary_color",
    "secondary_color",
    "accent_color",
    "font_family",
    "language",
    "timezone",
    "tonality",
    "voiceover",
    "avatar",
    "target_audience",
)
PROFILE_DEFAULTS = {
    "voiceover": "Warm owner voice",
    "avatar": "Owner-style avatar",
}
ALLOWED_TONALITIES = {"formal", "casual", "playful", "professional"}
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
LANGUAGE_RE = re.compile(r"^[a-zA-Z]{2,8}(?:[-_][a-zA-Z0-9]{2,8})?$")
TAG_RE = re.compile(r"<[^>]+>")
META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
LINK_TAG_RE = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("([^"]*)"|\'([^\']*)\')')


class CrawlError(Exception):
    def __init__(self, message, partial=None):
        super().__init__(message)
        self.message = message
        self.partial = partial


def _empty_profile():
    return {
        **{field: PROFILE_DEFAULTS.get(field, "") for field in PROFILE_FIELDS},
        "raw_extraction_json": {},
    }


def _strip_tags(value):
    text = html.unescape(str(value or ""))
    text = TAG_RE.sub(" ", text)
    return " ".join(text.split())


def _sanitize_text(value):
    return html.escape(_strip_tags(value), quote=False)


def _sanitize_url(value):
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        return ""
    return text


def _sanitize_color(value):
    text = str(value or "").strip()
    if not text or not HEX_COLOR_RE.match(text):
        return ""
    return text.lower()


def _sanitize_language(value):
    text = _strip_tags(value)
    if not text or not LANGUAGE_RE.match(text):
        return ""
    return text.lower().replace("_", "-")


def _sanitize_timezone(value):
    text = _strip_tags(value)
    if not text or text not in available_timezones():
        return ""
    return text


def _sanitize_tonality(value):
    text = _strip_tags(value).lower()
    return text if text in ALLOWED_TONALITIES else ""


def _sanitize_profile(payload, raw_extraction=None):
    payload = payload or {}
    sanitized = _empty_profile()
    for field in PROFILE_FIELDS:
        value = payload.get(field, "")
        if field == "logo_url":
            sanitized[field] = _sanitize_url(value)
        elif field.endswith("_color"):
            sanitized[field] = _sanitize_color(value)
        elif field == "language":
            sanitized[field] = _sanitize_language(value)
        elif field == "timezone":
            sanitized[field] = _sanitize_timezone(value)
        elif field == "tonality":
            sanitized[field] = _sanitize_tonality(value)
        else:
            sanitized[field] = _sanitize_text(value)
        if not sanitized[field] and field in PROFILE_DEFAULTS:
            sanitized[field] = PROFILE_DEFAULTS[field]
    sanitized["raw_extraction_json"] = raw_extraction if isinstance(raw_extraction, (dict, list)) else {}
    return sanitized


def _resolve_public_host(hostname, port):
    host = (hostname or "").strip().lower()
    if not host:
        raise CrawlError("Enter a valid public website URL.")
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise CrawlError("Private or local network URLs are not allowed.")
    try:
        ip = ipaddress.ip_address(host)
        addresses = [ip]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror:
            return
        addresses = []
        for info in infos:
            try:
                addresses.append(ipaddress.ip_address(info[4][0].split("%")[0]))
            except ValueError:
                continue
    for address in addresses:
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise CrawlError("Private or local network URLs are not allowed.")


def _validate_public_url(url):
    candidate = str(url or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise CrawlError("Enter a valid public website URL.")
    _resolve_public_host(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    return candidate


def fetch_homepage(url):
    safe_url = _validate_public_url(url)
    req = request.Request(
        safe_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as response:
            body = response.read(MAX_FETCH_BYTES + 1)
    except error.HTTPError as exc:
        raise CrawlError(f"Website returned HTTP {exc.code}.") from exc
    except error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, socket.timeout):
            raise CrawlError("Website request timed out.") from exc
        raise CrawlError("Website could not be reached.") from exc
    except (socket.timeout, TimeoutError):
        raise CrawlError("Website request timed out.")
    except ssl.SSLError as exc:
        raise CrawlError("Website SSL connection failed.") from exc
    except ValueError as exc:
        raise CrawlError("Enter a valid public website URL.") from exc
    if len(body) > MAX_FETCH_BYTES:
        body = body[:MAX_FETCH_BYTES]
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("latin-1", errors="ignore")


def _extract_attrs(tag):
    attrs = {}
    for key, _, double_quoted, single_quoted in ATTR_RE.findall(tag or ""):
        attrs[key.lower()] = html.unescape(double_quoted or single_quoted or "")
    return attrs


def clean_html_for_llm(html_text):
    source = str(html_text or "")
    if not source:
        return ""
    sections = []
    title_match = re.search(r"<title\b[^>]*>(.*?)</title>", source, re.IGNORECASE | re.DOTALL)
    if title_match:
        sections.append(f"Title: {_strip_tags(title_match.group(1))}")
    meta_lines = []
    for tag in META_TAG_RE.findall(source):
        attrs = _extract_attrs(tag)
        name = (attrs.get("name") or attrs.get("property") or "").strip().lower()
        content = _strip_tags(attrs.get("content"))
        if not content:
            continue
        if name == "description":
            meta_lines.append(f"description: {content}")
        elif name.startswith("og:"):
            meta_lines.append(f"{name}: {content}")
        elif name == "theme-color":
            meta_lines.append(f"theme-color: {content}")
    for tag in LINK_TAG_RE.findall(source):
        attrs = _extract_attrs(tag)
        rel = (attrs.get("rel") or "").lower()
        href = attrs.get("href") or ""
        if "icon" in rel and href:
            meta_lines.append(f"icon: {href}")
    if meta_lines:
        sections.append("Meta:\n" + "\n".join(meta_lines))
    json_ld = []
    for block in re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        source,
        re.IGNORECASE | re.DOTALL,
    ):
        cleaned = " ".join(html.unescape(block).split())
        if cleaned:
            json_ld.append(cleaned)
    if json_ld:
        sections.append("JSON-LD:\n" + "\n".join(json_ld))
    visible = re.sub(
        r"(?is)<(script|style|nav|header|footer|noscript|iframe)\b.*?</\1>",
        " ",
        source,
    )
    visible = re.sub(r"(?is)<!--.*?-->", " ", visible)
    visible = TAG_RE.sub(" ", visible)
    visible = " ".join(html.unescape(visible).split())
    if visible:
        sections.append("Body:\n" + visible)
    return "\n\n".join(section for section in sections if section)[:MAX_LLM_CHARS]


def _content_to_json(content):
    if isinstance(content, str):
        return json_loads(content, {})
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text") or "")
        return json_loads("".join(text_parts), {})
    if isinstance(content, dict):
        return content
    return {}


def extract_brand_profile(cleaned_text, *, api_key=None):
    api_key = api_key or os.environ.get("MINIMAX_API_KEY")
    if not cleaned_text or not api_key:
        return _empty_profile()
    payload = {
        "model": "MiniMax-M3",
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                "Extract a business brand profile from website content. "
                "Return one JSON object with exactly these string keys: "
                "name, description, industry, logo_url, primary_color, secondary_color, "
                "accent_color, font_family, language, timezone, tonality, voiceover, avatar, "
                "target_audience. "
                "Use empty strings when the website does not provide enough evidence."
            ),
            },
            {
                "role": "user",
                "content": cleaned_text,
            },
        ],
    }
    req = request.Request(
        MINIMAX_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, socket.timeout, TimeoutError, ValueError, OSError):
        return _empty_profile()
    try:
        message = ((body.get("choices") or [{}])[0].get("message") or {})
        raw_extraction = _content_to_json(message.get("content"))
        if not isinstance(raw_extraction, dict):
            return _empty_profile()
        return _sanitize_profile(raw_extraction, raw_extraction=raw_extraction)
    except (AttributeError, IndexError, TypeError, json.JSONDecodeError):
        return _empty_profile()
