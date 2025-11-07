from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AptekaSlonecznaPLSpider(Spider):
    name = "apteka_sloneczna_pl"
    item_attributes = {"brand": "Apteka Słoneczna", "brand_wikidata": "Q136708361"}
    start_urls = ["https://apteki-sloneczne.pl/nasze-apteki/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        locations = response.xpath('//div[contains(@class, "grid-col dmach-grid-item")]')

        for location in locations:
            item = Feature()
            item["city"] = location.xpath('.//span[contains(@class, "dmach_cat_")]/text()').get()
            item["street_address"] = location.xpath('.//p[contains(@class, "dmach-acf-value")]/text()').get()
            item["phone"] = location.xpath('.//a[contains(@class, "dmach-acf-value")]/text()').get()
            item["website"] = location.xpath('.//a[contains(@class, "et_pb_button")]/@href').get()

            opening_hours = location.xpath('.//span[contains(@class, "dmach-acf-value")]/text()').getall()
            oh = OpeningHours()
            for day, hours in zip(DAYS, opening_hours):
                oh.add_ranges_from_string(f"{day} {hours}")

            item["opening_hours"] = oh

            apply_category(Categories.PHARMACY, item)

            yield item
