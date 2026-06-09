from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class ScooterHutAUSpider(Spider):
    name = "scooter_hut_au"
    item_attributes = {"brand": "Scooter Hut", "brand_wikidata": "Q117747623", "extras": {"shop": "scooter"}}
    start_urls = ["https://scooterhut.com.au/pages/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//div[@class="store-details"]'):
            item = Feature()
            item["branch"] = store.xpath("./h3/text()").get("").replace("Scooter Hut", "").strip()
            item["ref"] = item["branch"]
            item["addr_full"] = (
                store.xpath('.//p[contains(text(), "Address")]/text()').get("").replace("Address:", "").strip()
            )
            item["email"] = store.xpath('.//a[starts-with(@href, "mailto:")]/@href').get("").replace("mailto:", "")
            item["phone"] = store.xpath('.//p[contains(text(), "Phone")]//a/text()').get()

            if destination := store.xpath('.//a[contains(@href, "destination=")]/@href').re_first(
                r"destination=([\d.-]+,[\d.-]+)"
            ):
                item["lat"], item["lon"] = destination.split(",")

            yield item
