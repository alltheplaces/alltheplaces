import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ThaiExpressCAUSSpider(SitemapSpider, StructuredDataSpider):
    name = "thai_express_ca_us"
    item_attributes = {
        "brand_wikidata": "Q7711610",
        "brand": "Thaï Express",
    }
    sitemap_urls = ["https://locations.thaiexpress.ca/sitemap.xml"]
    sitemap_rules = [(r"https://locations\.thaiexpress\.ca/(?:qc|on|ab|bc|ns|mb|sk|nb|nl|pe)/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        branch = re.sub(r"^Tha[iï] Express( Restaurant)?\s*", "", item.pop("name", "") or "").strip()
        item["branch"] = branch or None
        item["image"] = None

        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if '"GeoCoordinates"' not in ld:
                continue
            if geo := json.loads(ld).get("credentialSubject", {}).get("geo"):
                item["lat"], item["lon"] = geo.get("latitude"), geo.get("longitude")
                break

        apply_category(Categories.FAST_FOOD, item)
        yield item
