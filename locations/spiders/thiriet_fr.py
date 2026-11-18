from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ThirietFRSpider(CrawlSpider, StructuredDataSpider):
    name = "thiriet_fr"
    item_attributes = {"brand": "Thiriet", "brand_wikidata": "Q3524695"}
    start_urls = ["https://magasins.thiriet.com/"]
    rules = [
        # The first two rules navigate to the desired store directory.
        Rule(LinkExtractor(allow=r"/maison-thiriet-pres-de-chez-vous,[\d,]+\.html\??$")),
        Rule(LinkExtractor(allow=r"points-de-retrait,[\d,]+\.html\??$")),  # Store directory
        Rule(
            LinkExtractor(
                allow=r"points-de-retrait,[\d,]+\.html\?&vars=",
                restrict_xpaths='//*[@class="pagination"]//li[@class="active"]/following-sibling::li',
            )
        ),
        Rule(
            LinkExtractor(allow=r"/magasins/[-\w]+,[\d,]+\.html\?&args="),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url
        # The parameters are important as they base64-encode the ID for the shop
        item["ref"] = item["website"].split("args=")[-1]
        item["name"] = None
        if "/consigne-" in item["website"]:  # Frozen-food pickup locker, not a shop
            return
        else:
            apply_category(Categories.SHOP_FROZEN_FOOD, item)
        yield item
