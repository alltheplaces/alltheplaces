from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MedivetGBSpider(SitemapSpider, StructuredDataSpider):
    name = "medivet_gb"
    item_attributes = {"brand": "Medivet", "brand_wikidata": "Q120372623"}
    sitemap_urls = ["https://www.medivetgroup.com/sitemap.xml"]
    sitemap_rules = [(r"/vet-practices/(?!area/)([^/]+)/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        name = item.pop("name")
        if "closed" in name.lower():
            return

        item["branch"] = name.removeprefix("Medivet ").strip()
        item.pop("twitter", None)
        if item.get("facebook") == "https://www.facebook.com/Medivet.UK/":
            item.pop("facebook")

        apply_category(Categories.VETERINARY, item)

        yield item
