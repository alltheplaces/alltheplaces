from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DelTacoUSSpider(SitemapSpider, StructuredDataSpider):
    name = "del_taco_us"
    item_attributes = {"brand": "Del Taco", "brand_wikidata": "Q1183818"}
    allowed_domains = ["locations.deltaco.com"]
    sitemap_urls = ["https://locations.deltaco.com/robots.txt"]
    sitemap_rules = [(r"com/us/\w\w/[^/]+\/[^/]+$", "parse")]
    wanted_types = ["Restaurant"]
    json_parser = "chompjs"
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        specs = ld_data.get("openingHoursSpecification")
        for spec in [specs] if isinstance(specs, dict) else specs or []:
            if spec.get("opens") == "Open 24hs":
                spec["opens"], spec["closes"] = "12:00 AM", "11:59 PM"
                continue
            for key in ("opens", "closes"):
                if isinstance(spec.get(key), str):
                    spec[key] = spec[key].replace(".", "").strip()

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
