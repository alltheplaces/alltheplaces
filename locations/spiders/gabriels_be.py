from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

GABRIELS = {"brand": "Gabriëls", "brand_wikidata": "Q127602028"}
POWER = {"brand": "Power", "brand_wikidata": "Q98380874"}


class GabrielsBESpider(Spider):
    name = "gabriels_be"
    start_urls = ["https://www.gabriels.be/nl/tankstation-vinden"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@typeof="Place"]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["lat"] = location.xpath('.//meta[@property="latitude"]/@content').get()
            item["lon"] = location.xpath('.//meta[@property="longitude"]/@content').get()
            item["addr_full"] = location.xpath(
                './/div[contains(@class, "views-field-field-address-line")]/*[@class="field-content"]/text()'
            ).get()
            item["phone"] = location.xpath(
                './/div[contains(@class, "views-field-field-contact-phone")]//a/text()'
            ).get()
            item["email"] = location.xpath(
                './/div[contains(@class, "views-field-field-contact-email")]//a/text()'
            ).get()
            item["website"] = response.urljoin(
                location.xpath('.//div[contains(@class, "views-field-view-node")]//a/@href').get()
            )

            name = location.xpath(
                './/div[contains(@class, "views-field-title")]/*[@class="field-content"]/text()'
            ).get()

            if name.startswith("Gabriëls "):
                item["branch"] = name.removeprefix("Gabriëls ")
                item.update(GABRIELS)
            elif name.startswith("Power "):
                item["branch"] = name.removeprefix("Power ")
                item.update(POWER)

            apply_category(Categories.FUEL_STATION, item)

            yield item
