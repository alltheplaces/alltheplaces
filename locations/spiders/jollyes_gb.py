from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class JollyesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "jollyes_gb"
    item_attributes = {"brand": "Jollyes", "brand_wikidata": "Q45844955"}
    sitemap_urls = ["https://backend.jollyes.co.uk/media/sitemap-content.xml"]
    sitemap_rules = [(r"/store/", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for spec in ld_data.get("openingHoursSpecification", []):
            for key in ("opens", "closes"):
                if value := spec.get(key):
                    spec[key] = value.replace("::", ":")

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.split("/store/")[-1]
        item["branch"] = item.pop("name")
        item["twitter"] = None
        apply_category(Categories.SHOP_PET, item)
        yield item
