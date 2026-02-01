from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class WhittardGBSpider(Spider):
    name = "whittard_gb"
    item_attributes = {"brand": "Whittard of Chelsea", "brand_wikidata": "Q7996831"}

    def request_page(self, next_offset: int) -> Request:
        return Request(
            url=f"https://www.whittard.co.uk/stores?ajax=true&start={next_offset}",
            meta={"offset": next_offset},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.request_page(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('.//div[@class="store-row-container "]'):
            item = Feature()
            item["ref"] = location.xpath('.//div[@class="store-row grid-x location-cell"]/@data-storeid').get()
            item["lat"], item["lon"] = (
                location.xpath('.//span[@class="store-header"]/@data-lat').get(),
                location.xpath('.//span[@class="store-header"]/@data-lng').get(),
            )
            item["branch"] = location.xpath('.//span[@class="store-header"]//text()').get().strip()
            item["addr_full"] = clean_address(
                location.xpath('.//div[contains(@class, "store-details")]//text()').getall()
            )
            if phone := location.xpath('.//div[@class="contacts contacts-desktop"]/text()[2]').get():
                item["phone"] = phone.strip()
            item["website"] = location.xpath('.//a[contains(@href, "stores.whittard.co.uk")]//@href').get()

            apply_category(Categories.SHOP_TEA, item)

            yield item

        if "View More Stores" in response.text:
            yield self.request_page(response.meta["offset"] + 5)
