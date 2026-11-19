"""Contract tests for the tenant path normalizer.

These tests exercise the five public stubs in ``tenantfs.paths``.  They use
strings and pure path arithmetic only; no test touches the filesystem.
"""

import pytest

from tenantfs.paths import (
    InvalidPath,
    canonical_key,
    is_within,
    normalize,
    percent_decode,
    resolve,
)


def test_percent_decode_decodes_only_once():
    assert percent_decode("%252e%252e/secret") == "%2e%2e/secret"
    assert percent_decode("%zz/%2/%") == "%zz/%2/%"


def test_percent_encoded_dotdot_rejected():
    with pytest.raises(InvalidPath):
        resolve("acme", "%2e%2e/secret")
    with pytest.raises(InvalidPath):
        resolve("acme", "%2e%2e%2fsecret")


def test_semicolon_traversal_rejected():
    with pytest.raises(InvalidPath):
        resolve("acme", "..;/secret")


def test_nfc_nfd_share_canonical_key():
    nfc = "caf\u00e9/rapport.txt"
    nfd = "cafe\u0301/rapport.txt"
    assert normalize(nfc) == nfc
    assert normalize(nfd) == nfc
    assert canonical_key("acme", nfd) == canonical_key("acme", nfc)


def test_nul_rejected():
    with pytest.raises(InvalidPath):
        normalize("docs/evil\x00.txt")
    with pytest.raises(InvalidPath):
        resolve("acme", "docs/%00.txt")


def test_control_characters_rejected():
    for bad in ("docs/\x01.txt", "docs/\x1f.txt", "docs/\x7f.txt", "docs/\x85.txt"):
        with pytest.raises(InvalidPath):
            normalize(bad)


def test_trailing_dots_and_spaces_stripped():
    assert normalize("reports/quarter. . . ") == "reports/quarter"
    assert normalize("reports/notes.txt. ") == "reports/notes.txt"


def test_casefolded_when_case_insensitive():
    assert normalize("Reports/Q1.TXT", case_insensitive=True) == "reports/q1.txt"
    assert normalize("Reports/Q1.TXT") == "Reports/Q1.TXT"


def test_canonical_key_windows_aliases_same():
    keys = {
        canonical_key("acme", name)
        for name in ("A.txt", "a.txt", "a.txt. ", "A.TXT")
    }
    assert len(keys) == 1


def test_is_within_uses_segment_boundaries():
    assert is_within("/a/b", "/a/bc") is False
    assert is_within("/a/b", "/a/b/c") is True
    assert is_within("/a/b", "/a/b") is True
    assert is_within("/A/B", "/a/b/c", case_insensitive=True) is True


def test_dotdot_inside_root_resolves():
    assert normalize("a/b/../c") == "a/c"
    assert resolve("acme", "a/b/../c") == "/acme/a/c"


def test_dotdot_above_root_rejected():
    for bad in ("..", "../escape.txt", "a/../../escape.txt"):
        with pytest.raises(InvalidPath):
            normalize(bad)


def test_canonical_key_three_spellings_same():
    keys = {
        canonical_key("acme", "reports/2026/q1.txt"),
        canonical_key("acme", "reports//2026/./q1.txt"),
        canonical_key("acme", "reports\\2026\\q1.txt"),
    }
    assert len(keys) == 1


def test_invalid_tenant_and_absolute_path_rejected():
    for tenant in ("Acme", "-acme", "a", "a_b", "a" * 33):
        with pytest.raises(InvalidPath):
            resolve(tenant, "docs/a.txt")
    for path in ("/etc/passwd", "C:\\Windows\\a.txt", "\\\\server\\share\\a.txt"):
        with pytest.raises(InvalidPath):
            resolve("acme", path)


def test_resolve_returns_tenant_prefixed_path():
    assert resolve("acme-01", "docs/readme.txt") == "/acme-01/docs/readme.txt"
    assert (
        resolve("t1", "docs\\Q1.TXT", case_insensitive=True)
        == "/t1/docs/q1.txt"
    )
