from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NO, OpeningHours


class Rema1000NOSpider(Spider):
    name = "rema_1000_no"
    item_attributes = {"brand": "Rema 1000", "brand_wikidata": "Q28459"}
    allowed_domains = ["www.rema.no"]
    start_urls = ["https://www.rema.no/wp-json/rema-stores/v1/get-stores-data"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url)

    def build_store_website(self, location: dict, counties: dict) -> str | None:
        if not location.get("slug") or not location.get("countyName") or not location.get("municipalityName"):
            return None

        county_slug = None
        city_slug = None

        for county in counties.values():
            if county.get("name") != location["countyName"]:
                continue

            county_slug = county.get("slug")

            for city in county.get("cities", {}).values():
                if city.get("name") == location["municipalityName"]:
                    city_slug = city.get("slug")
                    break

            break

        if not county_slug or not city_slug:
            return None

        return "https://www.rema.no/butikker/{}/{}/{}".format(
            county_slug,
            city_slug,
            location["slug"],
        )

    def parse(self, response):
        response_data = response.json()

        for location in response_data["stores"]:
            item = DictParser.parse(location)
            item.pop("website", None)
            item["website"] = self.build_store_website(location, response_data.get("counties", {}))
            item["street_address"] = location.get("visitAddress")
            item["city"] = location.get("visitPlaceName")
            item["postcode"] = location.get("visitPostCode")
            item["state"] = location.get("countyName")

            hours_string = ""
            for day_name, day_hours in location.get("openingHours", {}).items():
                hours_string = "{} {}: {}".format(hours_string, day_name, day_hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, closed=CLOSED_NO)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
