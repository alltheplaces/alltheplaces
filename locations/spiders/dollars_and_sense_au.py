from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class DollarsAndSenseAUSpider(PlaywrightSpider):
    name = "dollars_and_sense_au"
    item_attributes = {"brand": "Dollars and Sense", "brand_wikidata": "Q133520267"}
    allowed_domains = ["www.dollarsense.au"]
    start_urls = ["https://www.dollarsense.au/pages/store-locations"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//*[@class="ds-location-card__meta"]'):
            item = Feature()
            item["branch"] = item["ref"] = store.xpath("./p/text()").get()
            item["addr_full"] = store.xpath("./p[2]/text()").get()
            item["phone"] = store.xpath("./p[3]/text()").get()
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            yield item
