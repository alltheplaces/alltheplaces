import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature

# Individual location pages are unstructured Divi page-builder HTML (no
# JSON-LD, no API), and the markup has drifted across several incompatible
# template revisions over the site's history (h1 vs h2 headings, "CONTACT"
# vs "CONTACT US", "Tel:" vs "Phone:", address/hours/contact sometimes
# split across sibling columns rather than a shared container, and even a
# typo'd "9HOURS" heading on one page). Rather than depend on a specific
# DOM shape, this walks all text nodes on the page in document order and
# locates the three landmark headings with a fuzzy prefix match, then
# treats everything between them as that section's content.
CLOSED_STRINGS = {"closed", "coming soon", "temporarily closed"}
AMENITY_KEYWORDS = (
    "dine-in",
    "dine in",
    "curbside",
    "delivery",
    "outdoor dining",
    "takeout",
    "pickup",
    "drive-thru",
    "drive thru",
)
JUNK_TEXT = {"get directions"}

HEADING_PATTERNS = {
    "STORE_INFO": [re.compile(r"^.{0,3}STORE\s*INFO\b\s*:?\s*", re.I)],
    "HOURS": [re.compile(r"^.{0,3}HOURS\b\s*:?\s*", re.I)],
    "CONTACT": [
        re.compile(r"^.{0,3}CONTACT\s+US\b\s*:?\s*", re.I),
        re.compile(r"^.{0,3}CONTACT\s*(?::|$)\s*", re.I),
    ],
}


def normalize(text: str) -> str:
    return " ".join(text.split())


def match_heading(text: str, category: str) -> tuple[bool, str | None]:
    for pattern in HEADING_PATTERNS[category]:
        if m := pattern.match(text):
            return True, text[m.end() :].strip()
    return False, None


def find_heading(texts: list[str], category: str, start: int = 0) -> tuple[int | None, str | None]:
    for i in range(start, len(texts)):
        matched, remainder = match_heading(texts[i], category)
        if matched:
            return i, remainder
    return None, None


class VitalityBowlsUSSpider(SitemapSpider):
    name = "vitality_bowls_us"
    item_attributes = {"brand": "Vitality Bowls", "brand_wikidata": "Q128583497"}
    sitemap_urls = ["https://vitalitybowls.com/sitemap.xml"]
    # "sunnyvale-old" is a stale duplicate of the "sunnyvale" page (same
    # address/phone, left over from a past site redesign); the negative
    # lookahead keeps it from being scraped as a second, separate location.
    sitemap_rules = [(r"/locations/(?!sunnyvale-old/)[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        texts = [normalize(t) for t in response.xpath("//body//text()").getall()]
        texts = [t for t in texts if t and t.lower() not in JUNK_TEXT]

        idx_si, si_remainder = find_heading(texts, "STORE_INFO")
        if idx_si is None:
            return
        idx_h, h_remainder = find_heading(texts, "HOURS", start=idx_si + 1)
        if idx_h is None:
            return
        idx_c, c_remainder = find_heading(texts, "CONTACT", start=idx_h + 1)
        if idx_c is None:
            return

        address = " ".join(p for p in ([si_remainder] if si_remainder else []) + texts[idx_si + 1 : idx_h] if p)
        if not address or address.lower() in CLOSED_STRINGS or not re.search(r"\d", address):
            return

        hours_lines = [h_remainder] if h_remainder else []
        for line in texts[idx_h + 1 : idx_c]:
            if any(keyword in line.lower() for keyword in AMENITY_KEYWORDS):
                break
            hours_lines.append(line)
        if any(line.strip().lower() in CLOSED_STRINGS for line in hours_lines):
            return

        contact = " ".join(([c_remainder] if c_remainder else []) + texts[idx_c + 1 : idx_c + 9])

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["addr_full"] = address

        # "Tel:"/"Phone:"/"Email:" labels aren't always present, and where
        # they are, phone/email don't always appear in the same order
        # (a few pages list email before phone), so each is matched by its
        # own shape rather than by a label.
        if m := re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", contact):
            item["phone"] = m.group(0)
        if m := re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", contact):
            item["email"] = m.group(0)

        oh = OpeningHours()
        for line in hours_lines:
            oh.add_ranges_from_string(line)
        item["opening_hours"] = oh

        extract_google_position(item, response)

        apply_category(Categories.FAST_FOOD, item)

        yield item
