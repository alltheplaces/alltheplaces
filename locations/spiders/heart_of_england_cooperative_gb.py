import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.central_england_cooperative import COOP_FOOD, set_operator

HEART_OF_ENGLAND_COOP = {"brand": "Heart of England Co-operative Society", "brand_wikidata": "Q5692254"}


class HeartOfEnglandCooperativeGBSpider(SitemapSpider):
    name = "heart_of_england_cooperative_gb"
    sitemap_urls = ["https://heartofengland.coop/store-sitemap.xml"]
    sitemap_rules = [(r"/store/[-\w]+/$", "parse_store")]
    requires_proxy = "GB"  # Cloudflare blocks non-GB requests

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        # The "image" and "addressLocality" values contain unescaped HTML, which breaks the JSON
        ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ld = re.sub(r'"(image|addressLocality)":\s*".*?",\n', "", ld, flags=re.DOTALL)
        item = LinkedDataParser.parse_ld(json.loads(ld), time_format="%I:%M %p")
        if not item["name"].startswith("Heart of England"):
            return
        item["website"] = response.url
        item["branch"] = re.sub(r"^Heart of England Co-?op\s*", "", item.pop("name"), flags=re.IGNORECASE)
        item.update(COOP_FOOD)
        set_operator(HEART_OF_ENGLAND_COOP, item)
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
