"""Tenant path normalization.

All entry points funnel through one pipeline: percent-decode exactly once,
NFC-normalize, resolve ``..`` segment-by-segment, apply Windows-style
trailing dot/space stripping, and optionally casefold.  ``canonical_key``
hashes the fully normalized segments so every spelling of the same logical
file shares one cache/quota/audit key.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import unquote_to_bytes


class InvalidPath(Exception):
    """Raised when a tenant or a path violates the path contract."""


_TENANT_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,31}")
_DRIVE_RE = re.compile(r"[A-Za-z]:")


def percent_decode(path: str) -> str:
    """Decode percent escapes in *path* exactly once.

    Valid ``%HH`` escapes are decoded once as UTF-8 bytes; ``+`` stays a
    literal plus.  Invalid or truncated escapes are preserved exactly.  The
    result is untrusted decoded text and must be passed to :func:`normalize`.
    """
    # unquote_to_bytes encodes literal characters as UTF-8, substitutes bytes
    # for valid %HH escapes, and passes invalid escapes through untouched.
    # surrogateescape keeps undecodable bytes lossless instead of rewriting
    # them to U+FFFD.
    return unquote_to_bytes(path).decode("utf-8", errors="surrogateescape")


def _check_control_chars(segment: str) -> None:
    for ch in segment:
        if unicodedata.category(ch) == "Cc":
            raise InvalidPath(f"control character in path segment: {segment!r}")


def normalize(relpath: str, case_insensitive: bool = False) -> str:
    r"""Return a canonical relative path for already-decoded text."""
    if relpath.startswith(("/", "\\")):
        raise InvalidPath(f"absolute path not allowed: {relpath!r}")
    if _DRIVE_RE.match(relpath):
        raise InvalidPath(f"drive-qualified path not allowed: {relpath!r}")

    relpath = unicodedata.normalize("NFC", relpath.replace("\\", "/"))

    segments: list[str] = []
    for raw in relpath.split("/"):
        if raw in ("", "."):
            continue
        if raw == "..":
            if not segments:
                raise InvalidPath(f"traversal above root: {relpath!r}")
            segments.pop()
            continue
        if raw.split(";", 1)[0] == "..":
            raise InvalidPath(f"traversal segment: {raw!r}")
        _check_control_chars(raw)
        stripped = raw.rstrip(" .")
        if not stripped:
            raise InvalidPath(f"segment strips to empty: {raw!r}")
        segments.append(stripped)

    if case_insensitive:
        segments = [seg.casefold() for seg in segments]
    return "/".join(segments)


def _validate_tenant(tenant: str) -> None:
    if not _TENANT_RE.fullmatch(tenant):
        raise InvalidPath(f"invalid tenant: {tenant!r}")


def resolve(tenant: str, relpath: str, case_insensitive: bool = False) -> str:
    """Resolve *relpath* inside *tenant* to an absolute canonical path."""
    _validate_tenant(tenant)
    normalized = normalize(percent_decode(relpath), case_insensitive)
    return "/" + tenant + "/" + normalized


def _split_absolute(path: str) -> list[str]:
    if not path.startswith("/"):
        raise InvalidPath(f"not an absolute path: {path!r}")
    segments = [seg for seg in path.split("/") if seg]
    for seg in segments:
        if seg in (".", ".."):
            raise InvalidPath(f"non-normalized segment in {path!r}")
    return segments


def is_within(root: str, path: str, case_insensitive: bool = False) -> bool:
    """Return whether *path* is *root* or a descendant of *root*."""
    root_segs = _split_absolute(root)
    path_segs = _split_absolute(path)
    if case_insensitive:
        root_segs = [seg.casefold() for seg in root_segs]
        path_segs = [seg.casefold() for seg in path_segs]
    if len(path_segs) < len(root_segs):
        return False
    return path_segs[: len(root_segs)] == root_segs


def canonical_key(tenant: str, relpath: str) -> str:
    r"""Return a stable deduplication/cache key for a tenant path."""
    _validate_tenant(tenant)
    normalized = normalize(percent_decode(relpath), case_insensitive=True)
    hashes = [
        hashlib.sha256(seg.encode("utf-8")).hexdigest()
        for seg in normalized.split("/")
        if seg
    ]
    return tenant + ":" + "/".join(hashes)
