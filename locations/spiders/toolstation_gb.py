import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ToolstationGBSpider(SitemapSpider, StructuredDataSpider):
    name = "toolstation_gb"
    item_attributes = {"brand": "Toolstation", "brand_wikidata": "Q7824103"}
    sitemap_urls = ["https://www.toolstation.com/sitemap/branches.xml"]
    wanted_types = ["HardwareStore"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        if name := item.pop("name", None):
            item["branch"] = name.removeprefix("Toolstation ")
        if street_address := item.get("street_address"):
            item["street_address"] = re.sub(r"^Toolstation\b[^,]*,?", "", street_address).strip(", ") or None
        item["ref"] = item["website"].rsplit("/", 1)[-1]
        item["phone"] = None

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
