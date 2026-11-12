"""Conservative editorial selection rules; not a factual verification service."""

import re


RUMOR_PATTERNS = (
    r"\brumou?rs?\b|\brumou?red\b|\brumou?ring\b",
    r"\bunconfirmed\b|\bunverified\b|\bspeculat(?:ion|ions|ive|ing|es?|ed)\b",
    r"\breportedly\b|\ballegedly\b|\bhearsay\b",
    r"\b(?:sources?|insiders?)\s+(?:say|says|said|claim|claims|suggest|suggests)\b",
    r"\baccording to\s+(?:(?:an?|the)\s+)?(?:unnamed|anonymous|industry|supply.chain)\s+sources?\b",
    r"\b(?:word on the street|take (?:this|it) with a grain of salt|i(?:'m| am) hearing)\b",
    r"傳聞|传闻|謠言|谣言|據傳|据传|網傳|网传|傳出|传出|盛傳|盛传|聽說|听说|未經證實|未经证实|尚未證實|尚未证实",
    r"據悉|据悉|知情人士|匿名人士|消息人士|業界傳言|业界传言|市場傳言|市场传言",
)
RUMOR_RE = re.compile("|".join(f"(?:{pattern})" for pattern in RUMOR_PATTERNS), re.IGNORECASE)


def rumor_signal(text):
    """Return the matched uncertainty marker, or None. Also skips denials."""
    match = RUMOR_RE.search(text or "")
    return match.group(0) if match else None


def prioritize_accounts(usernames):
    """Keep configured order, but consider Jukan only after other accounts."""
    return sorted(usernames, key=lambda name: name.lstrip("@").casefold() == "jukan05")
