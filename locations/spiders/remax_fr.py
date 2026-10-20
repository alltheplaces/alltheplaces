from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RemaxFRSpider(SitemapSpider, StructuredDataSpider):
    name = "remax_fr"
    item_attributes = {"brand": "RE/MAX", "brand_wikidata": "Q965845"}
    sitemap_urls = ["https://remax.fr/sitemap.xml"]
    sitemap_follow = ["offices_details_fr"]
    sitemap_rules = [(r"/fr/agence/[^/]+/(\d+)$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["ref"] = response.url.rsplit("/", 1)[-1]
        item["branch"] = (item.pop("name") or "").removeprefix("RE/MAX").strip()
        if city := item.get("city"):
            item["city"] = city.split(",")[-1].strip()
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
