from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FirstInterstateBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "first_interstate_bank_us"
    item_attributes = {"brand": "First Interstate Bank", "brand_wikidata": "Q5453107"}
    sitemap_urls = ["https://locations.firstinterstatebank.com/robots.txt"]
    sitemap_rules = [(r"https://locations.firstinterstatebank.com/\w\w/[^/]+/[^/]+\.html$", "parse")]
    wanted_types = ["BankOrCreditUnion"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        item["image"] = response.xpath('//img[@class="NAP-photo js-lazy"]/@src').get()
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Up Hours" in response.text)

        apply_category(Categories.BANK, item)

        yield item
