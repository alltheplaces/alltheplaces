import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Attendo elderly care homes (ikaihmisten hoivakodit, operator Attendo /
# Q11853322, NSI operator string) via the first-party sitemap; each home
# page carries a MedicalOrganization JSON-LD block with name, address and
# usually the home's own phone. 280 hoivakodit URLs as of 2026-10-14: 7 are
# Swedish-language duplicates of FI homes (6 "-sv" slugs plus milkasv;
# the slug half catches the "-sv" pages whatever their LD name (" sv"
# suffix, "vårdhem", fully Swedish); the name half catches milkasv) and
# drop; Kuisma (described as opening autumn 2026) advertises vacancies
# with full contact details, so included as operating.
# Emails are home-manager personal addresses (one even carries a soft
# hyphen); Facebook links are the brand handle or cross-link other homes
# (e.g. a Mummola link block on three unrelated homes): both dropped.
# No hours are published (residential care). Coords come from the
# server-rendered static-map pin (markers=), never the google.com place /
# search links; 0,0 (Kuisma, unset) and a mirrored lat==lon pair
# (Salmikoti) are dropped. Tanelintupa/Onni append ", NNNNN" to the street line,
# routed to postcode/street by content; Laurintupa's addressRegion holds
# municipality Laukaa and passes through untouched.


class AttendoFISpider(SitemapSpider, StructuredDataSpider):
    name = "attendo_fi"
    item_attributes = {"operator": "Attendo", "operator_wikidata": "Q11853322"}
    sitemap_urls = ["https://www.attendo.fi/sitemap.xml"]
    sitemap_rules = [(r"/hoivakodit/[^/]+/([^/]+)/?$", "parse_home")]
    wanted_types = ["MedicalOrganization"]
    drop_attributes = {"email", "facebook"}
    # Body tel:/mailto: links point at home managers or the footer hotline;
    # the home's own number is read from LD contactPoint below instead.
    search_for_phone = False

    STATICMAP_RE = re.compile(r"markers=[^&\"']*?(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
    POSTCODE_TAIL_RE = re.compile(r"^(?P<street>.*?),\s*(?P<postcode>\d{5})\s*$")

    def _stat(self, key: str) -> None:
        stats = getattr(getattr(self, "crawler", None), "stats", None)
        if stats is not None:
            stats.inc_value(f"atp/attendo_fi/{key}")

    def parse_home(self, response: TextResponse) -> Iterable[Feature]:
        yield from self.parse_sd(response)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        slug = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Slug half catches "-sv" pages whatever their LD name; name half catches milkasv (no "-sv"); leading space keeps Svengi.
        if slug.endswith("-sv") or str(ld_data.get("name", "")).casefold().endswith(" sv"):
            self._stat("dropped/swedish_duplicate")
            return
        contact = ld_data.get("contactPoint") or {}
        if isinstance(contact, list):  # Permitted by schema.org; unobserved in the feed.
            contact = contact[0] if contact else {}
        if isinstance(contact, dict) and contact.get("telephone"):
            item["phone"] = str(contact["telephone"])
        if match := self.STATICMAP_RE.search(response.text):
            lat, lon = float(match.group(1)), float(match.group(2))
            if lat == 0.0 and lon == 0.0:
                self._stat("coords/zero")
            elif lat == lon:
                self._stat("coords/mirrored")
            else:
                item["lat"], item["lon"] = lat, lon
        else:
            self._stat("coords/missing")
        if (street := item.get("street_address")) and (tail := self.POSTCODE_TAIL_RE.match(street)):
            if not item.get("postcode"):
                item["postcode"] = tail.group("postcode")
                self._stat("address/postcode_from_street")
            if item.get("postcode") == tail.group("postcode"):
                item["street_address"] = tail.group("street").strip()
            else:  # Street tail disagrees with the postcode field: keep street whole, count it.
                self._stat("address/postcode_mismatch")
        if not item.get("phone"):
            self._stat("empty/phone")
        if not item.get("postcode"):
            self._stat("empty/postcode")
        # Home-care service offices, not residential nursing homes.
        if "kotihoito" in str(item.get("name", "")).casefold():
            apply_category(Categories.SOCIAL_FACILITY, item)
        else:
            apply_category(Categories.NURSING_HOME, item)
        yield item
