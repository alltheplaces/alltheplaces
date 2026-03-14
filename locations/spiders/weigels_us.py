from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class WeigelsUSSpider(Spider):
    name = "weigels_us"
    item_attributes = {"brand": "Weigel's", "brand_wikidata": "Q7979844"}
    start_urls = ["https://weigels.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="location"]'):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["addr_full"] = location.xpath('.//*[@class="locationAddress"]/text()').get()
            item["phone"] = location.xpath('.//*[@class="locationHours"]/span/text()').get()
            item["website"] = location.xpath('.//*[@class="viewstore"]/a/@href').get()
            item["image"] = location.xpath(".//img/@src").get()

            services = location.xpath("@data-product-type").get().split(" ")

            apply_yes_no(Extras.ATM, item, "atm" in services)
            # TODO: Fuel types

            apply_category(Categories.FUEL_STATION, item)

            yield item
