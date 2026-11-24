"""Output renderers (Requirement 5)."""

import json

from sublist3r_reborn.models import (
    DnsRecords,
    EnumerationResult,
    SubdomainRecord,
    TakeoverAssessment,
    TakeoverStatus,
)
from sublist3r_reborn.output import render_table, result_to_dict, to_csv, to_json


def _sample_result() -> EnumerationResult:
    record = SubdomainRecord(
        name="blog.example.com",
        sources={"crtsh", "hackertarget"},
        dns=DnsRecords(a=["192.0.2.10"], aaaa=[], cname="user.github.io"),
        takeover=TakeoverAssessment(
            status=TakeoverStatus.POSSIBLE,
            provider="GitHub Pages",
            cname_target="user.github.io",
            reason="points to provider",
        ),
    )
    plain = SubdomainRecord(name="www.example.com", sources={"crtsh"})
    return EnumerationResult(
        domain="example.com",
        records=[record, plain],
        errors={"anubisdb": "boom"},
    )


def test_result_to_dict_structure():
    data = result_to_dict(_sample_result())
    assert data["domain"] == "example.com"
    assert data["count"] == 2
    assert data["errors"] == {"anubisdb": "boom"}
    first = data["subdomains"][0]
    assert first["name"] == "blog.example.com"
    assert first["sources"] == ["crtsh", "hackertarget"]
    assert first["dns"]["cname"] == "user.github.io"
    assert first["takeover"]["status"] == "possible"
    assert first["takeover"]["provider"] == "GitHub Pages"


def test_to_json_is_valid_json():
    parsed = json.loads(to_json(_sample_result()))
    assert parsed["count"] == 2
    assert parsed["subdomains"][1]["takeover"]["status"] == "none"


def test_to_csv_rows():
    lines = to_csv(_sample_result()).strip().splitlines()
    assert lines[0].startswith("name,sources,a,aaaa,cname,takeover_status")
    assert len(lines) == 3
    assert "blog.example.com" in lines[1]
    assert "user.github.io" in lines[1]
    assert "possible" in lines[1]


def test_render_table_contains_records():
    table = render_table(_sample_result())
    assert "SUBDOMAIN" in table
    assert "blog.example.com" in table
    assert "POSSIBLE" in table
    assert "www.example.com" in table
