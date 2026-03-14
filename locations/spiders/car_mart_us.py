from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CarMartUSSpider(Spider):
    name = "car_mart_us"
    item_attributes = {"brand_wikidata": "Q120636900"}
    start_urls = ["https://www.car-mart.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="loc"][@data-lotid]'):
            item = Feature()
            item["ref"] = location.xpath("@data-lotid").get()
            item["extras"]["ref:google:place_id"] = location.xpath("@data-place").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["website"] = response.urljoin(location.xpath("./h2/a/@href").get())
            item["phone"] = location.xpath('.//a[contains(@href, "tel")]/text()').get()
            item["branch"] = location.xpath("./h2/a/span/text()").get().removeprefix("CAR-MART of ")
            item["addr_full"] = merge_address_lines(
                location.xpath('.//div[@class="info"]/p/a[contains(@href, "google.com")]/text()').getall()
            )
            item["street_address"] = location.xpath(".//@data-lot-street").get()
            item["city"] = location.xpath(".//@data-lot-city").get()
            item["state"] = location.xpath(".//@data-lot-state").get()
            item["postcode"] = location.xpath(".//@data-lot-zip").get()

            apply_category(Categories.SHOP_CAR, item)

            yield item
