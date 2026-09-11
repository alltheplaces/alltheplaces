from typing import Iterable
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RapidPareBriseFRSpider(SitemapSpider, StructuredDataSpider):
    name = "rapid_pare_brise_fr"
    item_attributes = {"brand": "Rapid Pare-Brise", "brand_wikidata": "Q112064766"}
    sitemap_urls = ["https://www.rapidparebrise.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.rapidparebrise\.fr/.*-\d+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item.get("facebook") == "https://www.facebook.com/rapidparebrisefrance":
        	item["facebook"] = None
        
        item["branch"] = item.pop("name").removeprefix("Rapid Pare-Brise ")
        
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
