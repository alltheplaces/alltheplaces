import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RocEclercFRSpider(SitemapSpider, StructuredDataSpider):
    name = "roc_eclerc_fr"
    item_attributes = {"brand": "Roc-Eclerc", "brand_wikidata": "Q62558102"}
    sitemap_urls = ["https://roc-eclerc.com/sitemap/agences.xml"]
    # Agency pages end in an agency code; the other URLs are city landing pages.
    sitemap_rules = [(r"-fun_fra\w+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rsplit("-fun_", 1)[1]
        branch = re.sub(r"^pompes funèbres roc[ -]eclerc\s*", "", item["name"], flags=re.IGNORECASE)
        # Affiliated funeral homes keep their own name within the network.
        if branch != item["name"]:
            item["branch"] = branch
            del item["name"]
        apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
        yield item
