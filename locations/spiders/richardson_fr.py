from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RichardsonFRSpider(SitemapSpider, StructuredDataSpider):
    name = "richardson_fr"
    item_attributes = {"brand": "Richardson", "brand_wikidata": "Q3415192"}
    sitemap_urls = ["https://www.richardson.fr/stores/sitemap.xml"]
    sitemap_rules = [(r"https://www.richardson.fr/tous-les-magasins/agence/.*", "parse_sd")]
    wanted_types = ["HardwareStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/RichardsonFR/":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("RICHARDSON ")
        
        apply_category(Categories.SHOP_BATHROOM_FURNISHING, item)
        yield item
