from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.structured_data_spider import extract_phone


class KidStrongSpider(Spider):
    name = "kid_strong"
    item_attributes = {"brand": "KidStrong", "brand_wikidata": "Q125705878"}
    start_urls = ["https://www.kidstrong.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="locations__place place select-location active"]'):
            item = Feature()
            item["name"] = location.xpath("@data-name").get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-long").get()
            item["addr_full"] = location.xpath("@data-add").get()
            extract_phone(item, location)
            item["ref"] = item["website"] = response.urljoin(
                location.xpath('a[contains(@href, "/locations/")]/@href').get()
            )
            yield item
