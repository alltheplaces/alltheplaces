from json import loads
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class TileAfricaNAZASpider(AmastyStoreLocatorSpider):
    name = "tile_africa_na_za"
    item_attributes = {"brand": "Tile Africa", "brand_wikidata": "Q130413927"}
    start_urls = ["https://www.tileafrica.co.za/find-a-store"]
    hours = {}

    def parse(self, response: Response):
        for location in response.xpath(".//div[@data-amid]"):
            self.hours[location.xpath("@data-amid").get()] = location.xpath(
                'string(.//div[@class="amlocator-week"])'
            ).get()
        yield from self.parse_features(
            loads(
                response.xpath('//script[contains(text(), "Amasty_Storelocator")]/text()').re_first(
                    r"jsonLocations: ({.+}),"
                )
            )["items"]
        )

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Tile Africa ", "")
        for line in popup_html.xpath('//div[@class="amlocator-info-popup"]/text()').getall():
            line = line.strip()
            if line.startswith("Address: "):
                item["street_address"] = line.replace("Address: ", "")
            elif line.startswith("City: "):
                item["city"] = line.replace("City: ", "")
            elif line.startswith("Zip: "):
                item["postcode"] = line.replace("Zip: ", "")
            elif line.startswith("State: "):
                item["state"] = line.replace("State: ", "")
            elif line.startswith("Tel: "):
                item["phone"] = line.replace("Tel: ", "")

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(self.hours[str(item["ref"])])
        yield item
