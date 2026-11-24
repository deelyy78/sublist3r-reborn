"""Passive-source parser fixtures — all offline (Requirements 1.1/1.2)."""

import pytest

from sublist3r_reborn.sources.anubisdb import parse_anubisdb
from sublist3r_reborn.sources.crtsh import parse_crtsh
from sublist3r_reborn.sources.hackertarget import parse_hackertarget

CRTSH_BODY = """[
  {"name_value": "www.example.com", "common_name": "example.com"},
  {"name_value": "*.api.example.com\\napi.example.com", "common_name": "api.example.com"},
  {"name_value": "mail.example.com\\nmail.example.com", "common_name": "mail.example.com"},
  {"name_value": "unrelated.other.net", "common_name": "other.net"},
  {"name_value": 42, "common_name": null},
  "not-a-dict"
]"""


def test_parse_crtsh_extracts_all_names():
    names = parse_crtsh(CRTSH_BODY)
    assert "www.example.com" in names
    assert "api.example.com" in names  # newline-split out of name_value
    assert "*.api.example.com" in names  # raw wildcard kept; normaliser handles it
    assert "mail.example.com" in names
    assert "example.com" in names  # common_name apex: filtered later, not here
    assert "unrelated.other.net" in names  # scope filtering is the normaliser's job


def test_parse_crtsh_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_crtsh("<html>503 Service Unavailable</html>")


def test_parse_crtsh_non_list_is_empty():
    assert parse_crtsh('{"error": "slow"}') == set()


HACKERTARGET_BODY = """www.example.com,93.184.216.34
api.example.com,93.184.216.35
no-comma-line
,1.2.3.4
"""


def test_parse_hackertarget_extracts_hosts():
    assert parse_hackertarget(HACKERTARGET_BODY) == {
        "www.example.com",
        "api.example.com",
    }


def test_parse_hackertarget_error_output_is_empty():
    assert parse_hackertarget("error invalid host\n") == set()
    assert parse_hackertarget("No DNS A records found\n") == set()
    assert parse_hackertarget("") == set()


ANUBIS_BODY = '["www.example.com", "api.example.com", "www.example.com", 7, ""]'


def test_parse_anubisdb_extracts_hosts():
    assert parse_anubisdb(ANUBIS_BODY) == {"www.example.com", "api.example.com"}


def test_parse_anubisdb_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_anubisdb("not json")


def test_parse_anubisdb_non_list_is_empty():
    assert parse_anubisdb('{"subdomains": []}') == set()
