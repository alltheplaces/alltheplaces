import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BrightHorizonsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bright_horizons_gb"
    item_attributes = {
        "brand": "Bright Horizons",
        "brand_wikidata": "Q4967421",
    }
    allowed_domains = ["www.brighthorizons.co.uk"]
    sitemap_urls = ["https://www.brighthorizons.co.uk/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.brighthorizons\.co\.uk/our-nurseries/[-\w]+$", "parse_sd")]
    wanted_types = ["ChildCare"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if "Temporarily Closed" in response.text:
            return
        item["branch"] = re.sub(
            r"\s+Day Nursery (?:and|&) Preschool$", "", re.sub(r"^Bright Horizons(?: at)?\s+", "", item.pop("name"))
        )
        item.pop("email", None)
        if item.get("facebook") == "https://www.facebook.com/BrightHorizonsFamiliesUK":
            item.pop("facebook")
        apply_category(Categories.KINDERGARTEN, item)
        yield item
