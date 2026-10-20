import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Attendo elderly care homes via the first-party sitemap; each home page
# carries MedicalOrganization JSON-LD. Coords come from the server-rendered
# static-map pin (markers=), never google.com place/search links. Emails
# are per-manager personal addresses and Facebook links the brand handle
# or cross-links, so both drop via drop_attributes.


class AttendoFISpider(SitemapSpider, StructuredDataSpider):
    name = "attendo_fi"
    item_attributes = {"operator": "Attendo", "operator_wikidata": "Q11853322"}
    sitemap_urls = ["https://www.attendo.fi/sitemap.xml"]
    sitemap_rules = [(r"/hoivakodit/[^/]+/([^/]+)/?$", "parse_sd")]
    wanted_types = ["MedicalOrganization"]
    drop_attributes = {"email", "facebook"}
    # Body tel:/mailto: links point at home managers or the footer hotline;
    # the home's own number is read from LD contactPoint below instead.
    search_for_phone = False

    STATICMAP_RE = re.compile(r"markers=[^&\"']*?(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")
    POSTCODE_TAIL_RE = re.compile(r"^(?P<street>.*?),\s*(?P<postcode>\d{5})\s*$")

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        slug = response.url.rstrip("/").rsplit("/", 1)[-1]
        # Slug half catches "-sv" pages whatever their LD name; name half catches milkasv (no "-sv"); leading space keeps Svengi.
        if slug.endswith("-sv") or ld_data.get("name", "").casefold().endswith(" sv"):
            self.crawler.stats.inc_value("atp/attendo_fi/dropped/swedish_duplicate")
            return
        contact = ld_data.get("contactPoint") or {}
        if contact.get("telephone"):
            item["phone"] = contact["telephone"]
        if match := self.STATICMAP_RE.search(response.text):
            lat, lon = float(match.group(1)), float(match.group(2))
            if lat == 0.0 and lon == 0.0:
                self.crawler.stats.inc_value("atp/attendo_fi/coords/zero")
            elif lat == lon:
                self.crawler.stats.inc_value("atp/attendo_fi/coords/mirrored")
            else:
                item["lat"], item["lon"] = lat, lon
        if (street := item.get("street_address")) and (tail := self.POSTCODE_TAIL_RE.match(street)):
            if not item.get("postcode"):
                item["postcode"] = tail.group("postcode")
                self.crawler.stats.inc_value("atp/attendo_fi/address/postcode_from_street")
            if item.get("postcode") == tail.group("postcode"):
                item["street_address"] = tail.group("street")
        # Home-care service offices, not residential nursing homes.
        if "kotihoito" in item.get("name", "").casefold():
            apply_category(Categories.SOCIAL_FACILITY, item)
        else:
            apply_category(Categories.NURSING_HOME, item)
        yield item
