# -*- coding: utf-8 -*-
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsFRSpider(scrapy.Spider):
    name = "mcdonalds_fr"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.fr", "api.woosmap.com", "ws.mcdonalds.fr"]

    start_urls = [
        "https://api.woosmap.com/project/config?key=woos-77bec2e5-8f40-35ba-b483-67df0d5401be"
    ]
    headers = {
        "origin": "https://www.mcdonalds.fr",
    }

    day_range = {
        1: "Mo",
        2: "Tu",
        3: "We",
        4: "Th",
        5: "Fr",
        6: "Sa",
        7: "Su",
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://api.woosmap.com/project/config?key=woos-77bec2e5-8f40-35ba-b483-67df0d5401be",
            method="GET",
            callback=self.parse_store_grid,
            headers=self.headers,
        )

    def parse_store_grid(self, response):
        config_id = str(response.json().get("updated")).split(".", maxsplit=1)[0]

        # Scan the entire France map with zoom level 10. https://www.mcdonalds.fr/restaurants
        for lat in range(495, 540):
            for long in range(340, 379):
                yield scrapy.Request(
                    url=f"https://api.woosmap.com/tiles/10-{str(lat)}-{str(long)}.grid.json?key=woos-77bec2e5-8f40-35ba-b483-67df0d5401be&_={config_id}",
                    method="GET",
                    callback=self.get_store_ids,
                    headers=self.headers,
                )

    def get_store_ids(self, response):
        json_obj = response.json()
        for store in json_obj["data"]:
            store_id = json_obj["data"].get(store)["store_id"]
            yield scrapy.Request(
                url=f"https://ws.mcdonalds.fr/api/restaurant/{store_id}/?responseGroups=RG.RESTAURANT.FACILITIES",
                method="GET",
                callback=self.parse_all_stores,
                headers=self.headers,
            )

    def parse_all_stores(self, response):
        store_json = response.json()
        address_info = store_json["restaurantAddress"][0]
        coords = store_json["coordinates"]
        store_oh = store_json.get("openingHours")
        opening_hours = OpeningHours()
        for day in store_oh if len(store_json.get("openingHours")) > 0 else []:
            if day["beginHour"] != "":
                opening_hours.add_range(
                    self.day_range.get(day.get("day")),
                    day["beginHour"],
                    day["endHour"],
                )
        properties = {
            "name": f"McDonalds {store_json['name']}",
            "ref": address_info.get("id"),
            "addr_full": address_info.get("address1"),
            "city": address_info.get("city"),
            "postcode": address_info.get("zipCode"),
            "country": address_info.get("country"),
            "phone": store_json.get("phone"),
            "state": store_json.get("region"),
            "opening_hours": opening_hours.as_opening_hours(),
            "lat": coords.get("latitude"),
            "lon": coords.get("longitude"),
        }

        yield GeojsonPointItem(**properties)
