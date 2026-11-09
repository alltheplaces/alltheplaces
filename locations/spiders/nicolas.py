import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class NicolasSpider(SitemapSpider, StructuredDataSpider):
    name = "nicolas"
    item_attributes = {"brand": "Maison Nicolas", "brand_wikidata": "Q3340012"}
    sitemap_urls = ["https://www.nicolas.com/fr/fr/sitemap/sitemap-index_1-fr.xml"]
    sitemap_rules = [(r"/fr/fr/nos-boutiques/[^/]+/(\d+)\.html$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if branch := item.pop("name"):
            item["branch"] = re.sub(r"(?i)^nicolas[\s\-]+", "", branch).strip()
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
