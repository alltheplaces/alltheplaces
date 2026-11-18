import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MonceauFleursFRSpider(SitemapSpider, StructuredDataSpider):
    name = "monceau_fleurs_fr"
    item_attributes = {"brand": "Monceau Fleurs", "brand_wikidata": "Q17629431"}
    sitemap_urls = ["https://www.monceaufleurs.com/Assets/Rbs/Seo/100190/fr_FR/Rbs_Store_Store.1.xml"]
    sitemap_rules = [(r"/fleuriste/", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"facebook", "image"}
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^monceau fleurs[\s-]*", "", item.pop("name"), flags=re.IGNORECASE)
        apply_category(Categories.SHOP_FLORIST, item)
        yield item
