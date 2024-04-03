import json

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class WesolaPaniSpider(Spider):
    name = "wesola_pani"
    item_attributes = {"brand": "Wesoła Pani", "brand_wikidata": "Q123240454"}
    start_urls = ["https://wesolapani.com/shops"]

    def parse(self, response: Response, **kwargs):
        storage_js = response.xpath(
            '//script[contains(text(), "var storage") and not(contains(text(), "DOMContentLoaded"))]/text()'
        ).re_first(r"var storage = (.*);")
        storage = json.loads(storage_js)

        for shop in storage["shops"]:
            opening_hours = OpeningHours()
            opening_hours.add_ranges_from_string(ranges_string=shop["shedule"], days=DAYS_RU)

            yield Feature(
                {
                    "ref": shop["id"],
                    "lat": shop["posx"],
                    "lon": shop["posy"],
                    "phone": shop["phone1"],
                    "addr_full": clean_address(shop["address"]),
                    "opening_hours": opening_hours,
                }
            )
