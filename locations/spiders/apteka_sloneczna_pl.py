from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AptekaSlonecznaPLSpider(Spider):
    name = "apteka_sloneczna_pl"
    item_attributes = {"brand": "Apteka Słoneczna", "brand_wikidata": "Q136708361"}
    start_urls = ["https://apteki-sloneczne.pl/nasze-apteki/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[contains(@class, "grid-col dmach-grid-item")]'):
            item = Feature()
            item["city"] = location.xpath('.//span[contains(@class, "dmach_cat_")]/text()').get()
            item["street_address"] = location.xpath('.//p[contains(@class, "dmach-acf-value")]/text()').get()
            item["phone"] = location.xpath('.//a[contains(@class, "dmach-acf-value")]/text()').get()
            item["image"] = location.xpath(".//img/@src").get()
            item["ref"] = item["website"] = location.xpath('.//a[contains(@class, "et_pb_button")]/@href').get()

            item["opening_hours"] = self.parse_opening_hours(
                location.xpath('.//span[contains(@class, "dmach-acf-value")]/text()').getall()
            )

            apply_category(Categories.PHARMACY, item)

            yield Request(item["website"], self.parse_coords, cb_kwargs={"item": item})

    def parse_opening_hours(self, opening_hours) -> OpeningHours:
        oh = OpeningHours()
        for day, hours in zip(DAYS, opening_hours):
            if hours in "nieczynne":
                oh.set_closed(day)
            else:
                oh.add_range(day, *hours.replace(".", ":").replace(" ", "").split("-"))

        return oh

    def parse_coords(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        item["lat"] = response.xpath("//@data-center-lat").get()
        item["lon"] = response.xpath("//@data-center-lng").get()
        yield item
