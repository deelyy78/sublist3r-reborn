"""Takeover fingerprint matching and assessment logic (Requirement 4)."""

from sublist3r_reborn.models import TakeoverStatus
from sublist3r_reborn.takeover import assess_takeover, match_provider


def test_match_known_providers():
    assert match_provider("user.github.io").provider == "GitHub Pages"
    assert match_provider("myapp.herokuapp.com").provider == "Heroku"
    assert match_provider("bucket.s3.amazonaws.com").provider == "AWS S3"
    assert match_provider("site.azurewebsites.net").provider.startswith("Microsoft Azure")
    assert match_provider("app.netlify.app").provider == "Netlify"


def test_match_requires_label_boundary():
    # Substring lookalikes must NOT match (Requirement 4.5).
    assert match_provider("evilgithub.io") is None
    assert match_provider("notherokuapp.com") is None
    assert match_provider("github.io.evil.com") is None


def test_match_exact_suffix_host():
    assert match_provider("github.io") is not None


def test_match_unknown_provider():
    assert match_provider("cdn.example.net") is None


def test_assess_no_cname():
    result = assess_takeover(None, target_resolves=False)
    assert result.status is TakeoverStatus.NONE


def test_assess_unknown_cname_target():
    result = assess_takeover("lb.example.net", target_resolves=True)
    assert result.status is TakeoverStatus.NONE
    assert result.provider is None
    assert result.cname_target == "lb.example.net"


def test_assess_dangling_provider_is_likely():
    result = assess_takeover("gone.herokuapp.com", target_resolves=False)
    assert result.status is TakeoverStatus.LIKELY
    assert result.provider == "Heroku"


def test_assess_resolving_provider_is_possible():
    result = assess_takeover("user.github.io", target_resolves=True)
    assert result.status is TakeoverStatus.POSSIBLE
    assert result.provider == "GitHub Pages"


def test_assess_http_signature_is_likely_even_when_resolving():
    # GitHub Pages targets resolve at the provider edge even when the
    # underlying site does not exist; the error page is the real signal.
    result = assess_takeover(
        "user.github.io", target_resolves=True, http_signature_hit=True
    )
    assert result.status is TakeoverStatus.LIKELY
    assert "fingerprint" in result.reason
