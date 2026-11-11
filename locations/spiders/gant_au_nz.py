from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class GantAUNZSpider(PlaywrightSpider):
    name = "gant_au_nz"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    allowed_domains = ["gant.com.au"]
    start_urls = ["https://gant.com.au/pages/stores"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('//section[contains(@class,"ai-store-locator-")]'):
            country = location.xpath(".//@data-state-group").get()
            for store in location.xpath(".//article[contains(@class,'ai-store-locator-')]"):
                item = Feature()
                item["branch"] = store.xpath(".//h4/text()").get()
                item["addr_full"] = store.xpath(".//p//text()").get().split("\n\n", 1)[0]
                if country == "New Zealand":
                    item["country"] = "NZ"
                else:
                    item["country"] = "AU"
                apply_category(Categories.SHOP_CLOTHES, item)

                yield item
