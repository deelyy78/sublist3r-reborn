"""Normaliser edge cases (Requirement 2)."""

from sublist3r_reborn.normalize import normalize_domain, normalize_hostname

DOMAIN = "example.com"


def test_basic_subdomain():
    assert normalize_hostname("www.example.com", DOMAIN) == "www.example.com"


def test_case_and_trailing_dot():
    assert normalize_hostname("WWW.Example.COM.", DOMAIN) == "www.example.com"


def test_whitespace_stripped():
    assert normalize_hostname("  api.example.com  ", DOMAIN) == "api.example.com"


def test_wildcard_prefix_stripped():
    assert normalize_hostname("*.mail.example.com", DOMAIN) == "mail.example.com"


def test_apex_rejected():
    assert normalize_hostname("example.com", DOMAIN) is None


def test_out_of_scope_rejected():
    assert normalize_hostname("www.other.com", DOMAIN) is None
    assert normalize_hostname("example.com.evil.com", DOMAIN) is None
    # Suffix without a label boundary is not a subdomain.
    assert normalize_hostname("notexample.com", DOMAIN) is None
    assert normalize_hostname("wwwexample.com", DOMAIN) is None


def test_embedded_wildcard_rejected():
    assert normalize_hostname("*.example.com", DOMAIN) is None  # collapses to apex
    assert normalize_hostname("a.*.example.com", DOMAIN) is None


def test_invalid_hostnames_rejected():
    assert normalize_hostname("bad..dots.example.com", DOMAIN) is None
    assert normalize_hostname("-leading.example.com", DOMAIN) is None
    assert normalize_hostname("under_score.example.com", DOMAIN) is None
    assert normalize_hostname("has space.example.com", DOMAIN) is None
    assert normalize_hostname("", DOMAIN) is None


def test_deep_subdomain_ok():
    assert normalize_hostname("a.b.c.example.com", DOMAIN) == "a.b.c.example.com"


def test_domain_normalisation():
    assert normalize_domain(" Example.COM. ") == "example.com"
    # Domain argument itself is normalised before scope checks.
    assert normalize_hostname("www.example.com", "EXAMPLE.com.") == "www.example.com"
