from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BouyguesTelecomFRSpider(CrawlSpider, StructuredDataSpider):
    name = "bouygues_telecom_fr"
    item_attributes = {"brand": "Bouygues Telecom", "brand_wikidata": "Q581438"}
    start_urls = ["https://boutiques.bouyguestelecom.fr/"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@id="module-all-cities"]')),
        Rule(LinkExtractor(tags=["section"], attrs=["data-route-load-stores"])),
        Rule(LinkExtractor(restrict_xpaths='//*[@data-tracking="storeLink"]'), callback="parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("BOUYGUES TELECOM ")
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
