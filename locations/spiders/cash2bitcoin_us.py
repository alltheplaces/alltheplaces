from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class Cash2bitcoinUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cash2bitcoin_us"
    item_attributes = {"brand": "Cash2Bitcoin", "brand_wikidata": "Q135318196"}
    allowed_domains = ["locations.cash2bitcoin.com"]
    sitemap_urls = ["https://locations.cash2bitcoin.com/gd_place-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locations\.cash2bitcoin\.com\/locations\/[^\/]+\/$", "parse_sd")]

    def pre_process_data(self, ld_data: dict) -> None:
        if day_hours := ld_data.get("openingHours"):
            ld_data["openingHours"] = list(map(lambda x: x.replace("00:00-00:00", "00:00-23:59"), day_hours))

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("email", None)
        item.pop("phone", None)
        item.pop("facebook", None)
        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["currency:ETH"] = "yes"
        item["extras"]["currency:LTC"] = "yes"
        item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"
        yield item
