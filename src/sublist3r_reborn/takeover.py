"""Subdomain-takeover detection.

A subdomain is a takeover candidate when its CNAME points at a
third-party provider where unclaimed resources are a known risk. Evidence
is combined by the pure function :func:`assess_takeover`:

- the CNAME target does not resolve at all  -> ``likely`` (dangling)
- an HTTP response matches the provider's unclaimed-resource error
  signature                                  -> ``likely``
- the target resolves and no signature seen  -> ``possible``

The fingerprint table below is written from public knowledge of
takeover-prone services (the "can I take over XYZ" body of research);
matching is always on DNS label boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .models import TakeoverAssessment, TakeoverStatus


@dataclass(frozen=True)
class ProviderFingerprint:
    suffix: str
    provider: str
    http_signatures: tuple[str, ...] = ()


FINGERPRINTS: tuple[ProviderFingerprint, ...] = (
    ProviderFingerprint(
        "github.io", "GitHub Pages", ("There isn't a GitHub Pages site here",)
    ),
    ProviderFingerprint("herokuapp.com", "Heroku", ("No such app",)),
    ProviderFingerprint("s3.amazonaws.com", "AWS S3", ("NoSuchBucket",)),
    ProviderFingerprint(
        "s3-website-us-east-1.amazonaws.com", "AWS S3 Website", ("NoSuchBucket",)
    ),
    ProviderFingerprint(
        "s3-website-us-west-2.amazonaws.com", "AWS S3 Website", ("NoSuchBucket",)
    ),
    ProviderFingerprint("azurewebsites.net", "Microsoft Azure App Service"),
    ProviderFingerprint("cloudapp.net", "Microsoft Azure Cloud Services"),
    ProviderFingerprint("trafficmanager.net", "Microsoft Azure Traffic Manager"),
    ProviderFingerprint("netlify.app", "Netlify"),
    ProviderFingerprint("netlify.com", "Netlify"),
    ProviderFingerprint("gitlab.io", "GitLab Pages"),
    ProviderFingerprint("bitbucket.io", "Bitbucket Cloud"),
    ProviderFingerprint("wordpress.com", "WordPress.com"),
    ProviderFingerprint("tumblr.com", "Tumblr"),
    ProviderFingerprint(
        "myshopify.com", "Shopify", ("Sorry, this shop is currently unavailable",)
    ),
    ProviderFingerprint("pantheonsite.io", "Pantheon"),
    ProviderFingerprint("readthedocs.io", "Read the Docs"),
    ProviderFingerprint("surge.sh", "Surge"),
    ProviderFingerprint("ghost.io", "Ghost"),
    ProviderFingerprint("zendesk.com", "Zendesk"),
    ProviderFingerprint("statuspage.io", "Statuspage"),
    ProviderFingerprint("webflow.io", "Webflow"),
    ProviderFingerprint("helpscoutdocs.com", "Help Scout Docs"),
    ProviderFingerprint("uservoice.com", "UserVoice"),
)


def match_provider(hostname: str) -> ProviderFingerprint | None:
    """Return the fingerprint whose suffix matches ``hostname`` on a label
    boundary (longest suffix wins), or ``None``."""
    host = hostname.strip().lower().rstrip(".")
    best: ProviderFingerprint | None = None
    for fp in FINGERPRINTS:
        if host == fp.suffix or host.endswith("." + fp.suffix):
            if best is None or len(fp.suffix) > len(best.suffix):
                best = fp
    return best


def assess_takeover(
    cname_target: str | None,
    target_resolves: bool,
    http_signature_hit: bool = False,
) -> TakeoverAssessment:
    """Map evidence about a CNAME target to a takeover assessment (pure)."""
    if not cname_target:
        return TakeoverAssessment(reason="No CNAME record")
    fp = match_provider(cname_target)
    if fp is None:
        return TakeoverAssessment(
            cname_target=cname_target,
            reason="CNAME target is not a known takeover-prone provider",
        )
    if http_signature_hit:
        return TakeoverAssessment(
            status=TakeoverStatus.LIKELY,
            provider=fp.provider,
            cname_target=cname_target,
            reason=(
                f"HTTP response matches the {fp.provider} "
                "unclaimed-resource fingerprint"
            ),
        )
    if not target_resolves:
        return TakeoverAssessment(
            status=TakeoverStatus.LIKELY,
            provider=fp.provider,
            cname_target=cname_target,
            reason=(
                f"CNAME points to {fp.provider} but the target does not "
                "resolve (dangling CNAME)"
            ),
        )
    return TakeoverAssessment(
        status=TakeoverStatus.POSSIBLE,
        provider=fp.provider,
        cname_target=cname_target,
        reason=(
            f"CNAME points to third-party provider {fp.provider}; whether "
            "the hosted resource exists was not verified"
        ),
    )


async def probe_http_signature(
    client: httpx.AsyncClient,
    hostname: str,
    fingerprint: ProviderFingerprint,
    timeout: float = 8.0,
) -> bool:
    """Fetch ``hostname`` over HTTPS (then HTTP) and look for the
    provider's unclaimed-resource error signature in the response body.

    All transport errors are swallowed: a failed probe is "no signature".
    """
    if not fingerprint.http_signatures:
        return False
    for scheme in ("https", "http"):
        try:
            response = await client.get(
                f"{scheme}://{hostname}/",
                timeout=timeout,
                follow_redirects=False,
            )
        except httpx.HTTPError:
            continue
        body = response.text or ""
        return any(sig in body for sig in fingerprint.http_signatures)
    return False
