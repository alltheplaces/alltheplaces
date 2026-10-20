import json
import re
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.storefinders.yext import YextSpider

# Carvel uses Yext Pages for its store locator. Each location page embeds the
# full Yext entity document as a URL encoded JSON blob passed to
# decodeURIComponent, which carries more than the page's JSON-LD does (entity
# id, display coordinates and structured opening hours).


class CarvelUSSpider(SitemapSpider):
    name = "carvel_us"
    item_attributes = {"brand": "Carvel", "brand_wikidata": "Q5047520"}
    allowed_domains = ["locations.carvel.com"]
    sitemap_urls = ["https://locations.carvel.com/sitemap1.xml"]
    # State (/ny) and city (/ny/brooklyn) directory pages are skipped; location
    # pages have at least three path segments.
    sitemap_rules = [(r"^https://locations\.carvel\.com/[a-z]{2}/[^/]+/[^/]+", "parse")]

    def parse(self, response, **kwargs):
        if not (blob := re.search(r'decodeURIComponent\("(.*?)"\)', response.text, re.S)):
            return
        location = json.loads(unquote(blob.group(1)))["document"]

        if location.get("closed"):
            return

        item = DictParser.parse(location)
        item["ref"] = location["id"]
        item["branch"] = location.get("address", {}).get("city")
        item["name"] = None
        item["street_address"] = " ".join(
            filter(None, [location["address"].get("line1"), location["address"].get("line2")])
        )
        item["phone"] = location.get("mainPhone")
        item["website"] = response.url
        item["lat"] = location.get("yextDisplayCoordinate", {}).get("latitude")
        item["lon"] = location.get("yextDisplayCoordinate", {}).get("longitude")

        if hours := location.get("hours"):
            item["opening_hours"] = YextSpider.parse_opening_hours(hours)

        apply_category(Categories.ICE_CREAM, item)

        yield item
