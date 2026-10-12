from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AlnaturaDESpider(SitemapSpider, StructuredDataSpider):
    name = "alnatura_de"
    item_attributes = {"brand": "Alnatura", "brand_wikidata": "Q876811"}
    allowed_domains = ["www.alnatura.de"]
    sitemap_urls = ["https://www.alnatura.de/sitemap/markets-de-de.xml"]
    sitemap_rules = [(r"/marktfinder/.+-(\d+)$", "parse")]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"
    drop_attributes = {"facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Alnatura Super Natur Markt ").strip()
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
