"""Tenant path normalization contract and stubs.

This module is intentionally unimplemented.  The five public functions below
define the contract that the task must implement; every one currently raises
``NotImplementedError`` so that the contract tests start red.
"""

from __future__ import annotations


class InvalidPath(Exception):
    """Raised when a tenant or a path violates the path contract."""


def percent_decode(path: str) -> str:
    """Decode percent escapes in *path* exactly once.

    Contract:
    - A valid ``%HH`` escape is decoded once as UTF-8 bytes.  ``%2e`` becomes
      ``.`` and ``%2f`` becomes ``/``; ``+`` is a literal plus, not a space.
    - Decoding is never recursive.  ``"%252e%252e"`` becomes ``"%2e%2e"``;
      the result must not be decoded a second time.
    - Invalid or truncated escapes (``"%"``, ``"%2"``, ``"%zz"``) are
      preserved exactly as supplied.
    - The return value is untrusted decoded text.  It may contain separators,
      traversal segments, NUL, or control characters, so callers must pass it
      to :func:`normalize`.  :func:`resolve` and :func:`canonical_key` perform
      this single decode at their entry boundary.
    """
    raise NotImplementedError


def normalize(relpath: str, case_insensitive: bool = False) -> str:
    r"""Return a canonical relative path.

    *relpath* is already-decoded text, not a URL.  This function never calls
    :func:`percent_decode`; percent decoding happens exactly once at an entry
    point.  Contract:
    - Only relative paths are accepted.  Paths beginning with ``/`` or ``\``,
      UNC paths, and drive-qualified paths such as ``C:\...`` or ``C:...``
      raise :class:`InvalidPath`.
    - Convert both ``\`` and ``/`` to ``/`` as segment separators, apply
      Unicode NFC, drop empty and ``.`` segments, and resolve internal ``..``
      segments one path segment at a time.
    - A ``..`` that would move above the relative root raises
      :class:`InvalidPath`.  String replacement of ``..`` is not permitted.
    - A segment whose text before the first ``;`` is exactly ``..`` is a
      traversal attempt (for example ``..;`` or ``..;/secret``) and raises
      :class:`InvalidPath`.
    - NUL and every Unicode ``Cc`` control character raise
      :class:`InvalidPath`.
    - Strip trailing ASCII spaces and dots from every segment using Windows
      filename semantics, so ``"A.txt. "`` becomes ``"A.txt"``.  A non-empty
      segment that becomes empty only because of this stripping is invalid.
    - With ``case_insensitive=True``, casefold each remaining segment.  With
      ``False``, preserve the NFC-cased spelling.
    - Return the surviving segments joined with ``/``, with no leading or
      trailing slash.  Empty input and ``.`` normalize to ``""``.
    """
    raise NotImplementedError


def resolve(tenant: str, relpath: str, case_insensitive: bool = False) -> str:
    """Resolve *relpath* inside *tenant* to an absolute canonical path.

    Contract:
    - ``tenant`` must match ``^[a-z0-9][a-z0-9-]{1,31}$``; otherwise raise
      :class:`InvalidPath`.
    - Percent-decode *relpath* exactly once with :func:`percent_decode`, then
      normalize the decoded text with :func:`normalize`, forwarding
      ``case_insensitive``.  Do not decode twice.
    - Any invalid tenant, absolute path, traversal, NUL, or control character
      raises :class:`InvalidPath`.
    - Return ``"/" + tenant + "/" + normalized``.  The result begins with
      ``/``; for a non-empty normalized path it has no trailing slash.
    """
    raise NotImplementedError


def is_within(root: str, path: str, case_insensitive: bool = False) -> bool:
    """Return whether *path* is *root* or a descendant of *root*.

    Contract:
    - Both arguments are absolute, already-normalized slash paths such as
      ``"/acme/docs"``.  Relative paths or paths containing ``.`` or ``..``
      segments are invalid and raise :class:`InvalidPath`.
    - Compare whole path segments, never string prefixes: ``"/a/bc"`` is not
      within ``"/a/b"``, while ``"/a/b/c"`` is.  Equal paths are within.
    - Ignore duplicate separators and a trailing slash while splitting.
    - Root ``"/"`` contains every valid absolute path.
    - With ``case_insensitive=True``, casefold each segment on both sides
      before comparison; with ``False``, compare exactly.
    """
    raise NotImplementedError


def canonical_key(tenant: str, relpath: str) -> str:
    r"""Return a stable deduplication/cache key for a tenant path.

    Contract:
    - Tenant validation is identical to :func:`resolve`; invalid tenants
      raise :class:`InvalidPath`.
    - Percent-decode *relpath* exactly once and normalize it with
      ``case_insensitive=True``.  Thus NFC/NFD spellings, ``A.txt`` /
      ``a.txt`` / ``a.txt.``, ``/`` versus ``\``, empty segments, and ``.``
      segments all collapse before hashing.
    - Hash each normalized segment with SHA-256 (hex) and join the hashes
      with ``/``.  Prefix the result with the tenant and ``":"``, for example
      ``"acme:<sha256(segment)>/<sha256(segment)>"``.  Do not use Python's
      salted ``hash()`` and do not use the raw input string as the key.
    - The same logical path must always map to the same key, regardless of
      spelling; different tenants must not collide.
    """
    raise NotImplementedError
