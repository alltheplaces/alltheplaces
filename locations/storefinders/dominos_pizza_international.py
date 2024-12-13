from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_coordinates
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class DominosPizzaInternationalSpider(JSONBlobSpider):
    dataset_attributes = {"source": "api", "api": "dominos_pizza"}

    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "Stores"

    domain = "order.golo03.dominos.com"
    region_code: str
    dpz_market: str
    dpz_language = "en"
    days = DAYS_EN
    city_search = False  # JM needs this
    additional_headers = {}  # AE needs this
    search_radius: int | None = None  # HR and SK need this, at least MX must not have this

    def start_requests(self):
        headers = {"DPZ-Language": self.dpz_language, "DPZ-Market": self.dpz_market} | self.additional_headers
        if self.city_search:
            url = f"https://order.golo01.dominos.com/store-locator-international/locations/city?regionCode={self.region_code}"
            yield JsonRequest(url=url, headers=headers, callback=self.parse_cities)
        coordinates = [coords for country, coords in country_coordinates(True).items() if country == self.region_code]
        for lat, lon in coordinates:
            url = f"https://{self.domain}/store-locator-international/locate/store?regionCode={self.region_code}&latitude={lat}&longitude={lon}"
            if self.search_radius is not None:
                url = url + f"&Radius={self.search_radius}"
            yield JsonRequest(url=url, headers=headers, callback=self.parse)

    def parse_cities(self, response):
        for city in response.json():
            headers = {"DPZ-Language": self.dpz_language, "DPZ-Market": self.dpz_market}
            url = f"https://order.golo01.dominos.com/store-locator-international/locate/store?regionCode={self.region_code}&City={city['name']}"
            yield JsonRequest(url=url, headers=headers, callback=self.parse)

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.process_store(item, response, feature) or []

    def process_store(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        if item["lat"] is None and location.get("StoreCoordinates") is not None:
            item["lat"] = location["StoreCoordinates"].get("StoreLatitude")
        if item["lon"] is None and location.get("StoreCoordinates") is not None:
            item["lon"] = location["StoreCoordinates"].get("StoreLongitude")
        if address_description := location["AddressDescription"]:
            item["addr_full"] = clean_address(address_description)
        item["country"] = self.region_code
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street")

        apply_yes_no(Extras.DELIVERY, item, location.get("AllowDeliveryOrders"))
        apply_yes_no(Extras.TAKEAWAY, item, location.get("AllowCarryoutOrders"))

        if hours := location.get("HoursDescription"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours, days=self.days)

        if location.get("ServiceHoursDescription") is not None and (
            delivery_hours := location["ServiceHoursDescription"].get("Delivery")
        ):
            oh = OpeningHours()
            oh.add_ranges_from_string(delivery_hours, days=self.days)
            item["extras"]["opening_hours:delivery"] = oh.as_opening_hours()

        if languages := location["LanguageTranslations"]:
            if "" in languages:
                languages.pop("")
            if len(languages) > 1:
                for language, info in languages.items():
                    item["extras"][f"branch:{language}"] = info["StoreName"]

        yield from self.post_process_item(item, response, location) or []
