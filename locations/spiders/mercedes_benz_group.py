from copy import deepcopy
from typing import Iterable

from geonamescache import GeonamesCache
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MercedesBenzGroupSpider(JSONBlobSpider):
    name = "mercedes_benz_group"

    BRAND_MAPPING = {
        "Mercedes-Benz": {"brand": "Mercedes-Benz", "brand_wikidata": "Q36008"},
        "Mercedes-Benz Vans": {"brand": "Mercedes-Benz Vans", "brand_wikidata": "Q55383469"},
        "Mercedes-Benz Trucks": {"brand": "Mercedes-Benz Trucks", "brand_wikidata": "Q36008"},
        "Maybach": {"brand": "Maybach", "brand_wikidata": "Q35989"},
        "Smart": {"brand": "Smart", "brand_wikidata": "Q156490"},
        "Fuso": {"brand": "Fuso", "brand_wikidata": "Q36033"},
        "Setra": {"brand": "Setra", "brand_wikidata": "Q938615"},
    }

    MERCEDES_BENZ = {"brand": "Mercedes-Benz", "brand_wikidata": "Q36008"}
    MERCEDES_BENZ_VANS = {"brand": "Mercedes-Benz Vans", "brand_wikidata": "Q55383469"}
    MERCEDES_BENZ_TRUCKS = {"brand": "Mercedes-Benz Trucks", "brand_wikidata": "Q36008"}
    SETRA = {"brand": "Setra", "brand_wikidata": "Q938615"}

    DEPARTMENT_MAPPING = {
        ("Mercedes-Benz", "New Vehicle Sales", "Passenger Car"): (MERCEDES_BENZ, Categories.SHOP_CAR),
        ("Mercedes-Benz", "New Vehicle Sales", "Vans"): (MERCEDES_BENZ_VANS, Categories.SHOP_CAR),
        ("Mercedes-Benz", "New Vehicle Sales", "Trucks"): (MERCEDES_BENZ_TRUCKS, Categories.SHOP_TRUCK),
        ("Mercedes-Benz", "New Vehicle Sales", "Busses"): (MERCEDES_BENZ, Categories.SHOP_BUS),
        ("Mercedes-Benz", "Repair & Maintenance", "Passenger Car"): (MERCEDES_BENZ, Categories.SHOP_CAR_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Vans"): (MERCEDES_BENZ_VANS, Categories.SHOP_CAR_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Trucks"): (MERCEDES_BENZ_TRUCKS, Categories.SHOP_TRUCK_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Busses"): (MERCEDES_BENZ, Categories.SHOP_BUS_REPAIR),
        ("Setra", "New Vehicle Sales", "Busses"): (SETRA, Categories.SHOP_BUS),
        ("Setra", "Repair & Maintenance", "Busses"): (SETRA, Categories.SHOP_BUS_REPAIR),
    }
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-apikey": "ce7d9916-6a3d-407a-b086-fea4cbae05f6"}}
    locations_key = "dealers"

    def make_request(self, country: str, page: int = 1) -> Request:
        url = "https://api.oneweb.mercedes-benz.com/dms-plus/v3/api/dealers/market?marketCode={}&page={}&size=25&includeFields=*&localeLanguage=true".format(
            country, page
        )
        return Request(url, meta={"country": country})

    def start_requests(self) -> Iterable[Request]:
        countries = GeonamesCache().get_countries().keys()
        for country in countries:
            yield self.make_request(country)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["outletId"]
        item["state"] = feature.get("address", {}).get("region", {}).get("state")
        country = response.meta["country"]
        for service in feature.get("offeredServices", []):
            key = (
                service.get("brand", {}).get("name"),
                service.get("service", {}).get("name"),
                service.get("productGroup", {}).get("name"),
            )
            self.crawler.stats.inc_value(f"{self.name}/services/{country}/{key[0]}/{key[1]}/{key[2]}")
            if key in self.DEPARTMENT_MAPPING:
                branded_item = deepcopy(item)
                brand, category = self.DEPARTMENT_MAPPING[key]
                branded_item.update(brand)
                apply_category(category, branded_item)
                yield branded_item

        data = response.json()
        current_page = data["page"]["number"]
        if current_page < data["page"]["totalPages"]:
            yield self.make_request(country, current_page + 1)

    def parse_contacts(self, item: Feature, service: dict) -> None:
        communication = service.get("communication", {})
        item["website"] = communication.get("INTERNET")
        item["email"] = communication.get("EMAIL")
        item["phone"] = communication.get("PHONE")

    def parse_hours(self, item: Feature, service: dict) -> None:
        if hours := service.get("openingHours"):
            oh = OpeningHours()
            for day in hours:
                if day.get("closed"):
                    oh.set_closed(day["day"])
                else:
                    for period in day.get("periods", []):
                        oh.add_range(day["day"], period["from"], period["until"])
            item["opening_hours"] = oh
