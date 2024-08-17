from scrapy import Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class DebonairsPizzaZASpider(Spider):
    name = "debonairs_pizza_za"
    item_attributes = {"brand": "Debonairs Pizza", "brand_wikidata": "Q65079407", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["app.debonairspizza.co.za"]
    start_urls = ["https://app.debonairspizza.co.za/management/api/store/locations"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_location_list)

    def parse_location_list(self, response):
        store_id_list = []
        for province in response.json():
            for city in province.get("Areas", []):
                for store in city.get("Stores", []):
                    store_id_list.append(store["Id"])
        for start_pos in range(0, len(store_id_list), 20):
            batch = store_id_list[start_pos : start_pos + 20]
            yield JsonRequest(
                url="https://app.debonairspizza.co.za/management/api/stores?ids={}".format(",".join(map(str, batch))),
                callback=self.parse_locations,
            )

    def parse_locations(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location.get("AddressLine1"), location.get("AddressLine2")])
            item.pop("state", None)
            item["website"] = "https://app.debonairspizza.co.za/restaurant/{}/{}".format(
                item["ref"], unidecode(item["name"].lower()).replace(" ", "-")
            )
            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("TradingHours", []):
                item["opening_hours"].add_range(
                    DAYS_3_LETTERS_FROM_SUNDAY[day_hours["Day"]],
                    day_hours["OpenTime"],
                    day_hours["CloseTime"],
                    "%H:%M:%S",
                )
            item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
            yield item
