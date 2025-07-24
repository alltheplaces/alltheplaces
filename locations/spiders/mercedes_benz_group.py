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
    """
    Main site: https://www.mercedes-benz.com/en/
    API found at https://www.mercedes-benz.dk/passengercars/mercedes-benz-cars/dealer-locator.html
    """

    name = "mercedes_benz_group"

    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-apikey": "ce7d9916-6a3d-407a-b086-fea4cbae05f6"}}
    locations_key = "dealers"

    MERCEDES_BENZ = {"brand": "Mercedes-Benz", "brand_wikidata": "Q36008"}
    MERCEDES_BENZ_VANS = {"brand": "Mercedes-Benz Vans", "brand_wikidata": "Q55383469"}
    MERCEDES_BENZ_TRUCKS = {"brand": "Mercedes-Benz Trucks", "brand_wikidata": "Q36008"}
    MERCEDES_BENZ_BUS = {"brand": "Mercedes-Benz Buses", "brand_wikidata": "Q1427345"}
    SETRA = {"brand": "Setra", "brand_wikidata": "Q938615"}
    FUSO = {"brand": "Fuso", "brand_wikidata": "Q1190247"}
    SMART = {"brand": "Smart", "brand_wikidata": "Q156490"}
    OMNI_PLUS = {"brand": "OMNIplus", "brand_wikidata": "Q122922653"}

    # Each location can have multiple services, each with a brand and product group.
    # Easiest way to work with this data downstream is to yield a POI for each brand/category combination.
    # This mapping is a way to manage this.
    DEPARTMENT_MAPPING: dict[tuple[str, str, str], tuple[dict, Categories | dict]] = {
        # key = (brand, service, productGroup):
        ("Mercedes-Benz", "New Vehicle Sales", "Passenger Car"): (MERCEDES_BENZ, Categories.SHOP_CAR),
        ("Mercedes-Benz", "New Vehicle Sales", "Vans"): (MERCEDES_BENZ_VANS, Categories.SHOP_CAR),
        ("Mercedes-Benz", "New Vehicle Sales", "Trucks"): (MERCEDES_BENZ_TRUCKS, Categories.SHOP_TRUCK),
        ("Mercedes-Benz", "New Vehicle Sales", "Busses"): (MERCEDES_BENZ_BUS, Categories.SHOP_BUS),
        ("Mercedes-Benz", "Repair & Maintenance", "Passenger Car"): (MERCEDES_BENZ, Categories.SHOP_CAR_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Vans"): (MERCEDES_BENZ_VANS, Categories.SHOP_CAR_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Trucks"): (MERCEDES_BENZ_TRUCKS, Categories.SHOP_TRUCK_REPAIR),
        ("Mercedes-Benz", "Repair & Maintenance", "Busses"): (MERCEDES_BENZ_BUS, Categories.SHOP_BUS_REPAIR),
        ("Mercedes-Benz", "Mercedes-Benz Rent", "Passenger Car"): (MERCEDES_BENZ, Categories.CAR_RENTAL),
        ("Mercedes-Benz", "Mercedes-Benz Rent", "Vans"): (MERCEDES_BENZ_VANS, Categories.CAR_RENTAL),
        ("Setra", "New Vehicle Sales", "Busses"): (SETRA, Categories.SHOP_BUS),
        ("Setra", "Repair & Maintenance", "Busses"): (SETRA, Categories.SHOP_BUS_REPAIR),
        ("FUSO", "New Vehicle Sales", "Trucks"): (FUSO, Categories.SHOP_TRUCK),
        ("FUSO", "Repair & Maintenance", "Trucks"): (FUSO, Categories.SHOP_TRUCK_REPAIR),
        ("smart", "New Vehicle Sales", "Passenger Car"): (SMART, Categories.SHOP_CAR),
        ("smart", "Repair & Maintenance", "Passenger Car"): (SMART, Categories.SHOP_CAR_REPAIR),
        ("smart", "Mercedes-Benz Rent", "Passenger Car"): (SMART, Categories.CAR_RENTAL),
        ("Mercedes-Benz", "OMNIplus BusPort", "Busses"): (OMNI_PLUS, Categories.SHOP_BUS_REPAIR),
        ("Mercedes-Benz", "OMNIplus BusWorld", "Busses"): (OMNI_PLUS, Categories.SHOP_BUS_REPAIR),
        ("Setra", "OMNIplus BusPort", "Busses"): (OMNI_PLUS, Categories.SHOP_BUS_REPAIR),
        ("Setra", "OMNIplus BusWorld", "Busses"): (OMNI_PLUS, Categories.SHOP_BUS_REPAIR),
    }

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

        # Similar to how it's shown on the website
        item["name"] = feature.get("legalName")
        item["extras"]["alt_name"] = feature.get("nameAddition")

        item["state"] = feature.get("address", {}).get("region", {}).get("state")
        item["lat"] = feature.get("address", {}).get("coordinates", {}).get("latitude")
        item["lon"] = feature.get("address", {}).get("coordinates", {}).get("longitude")
        country = response.meta["country"]
        for service in feature.get("offeredServices", []):
            if service.get("validity", {}).get("validity") is False:
                continue
            key = (
                service.get("brand", {}).get("name"),
                service.get("service", {}).get("name"),
                service.get("productGroup", {}).get("name"),
            )
            # Useful in development:
            # self.crawler.stats.inc_value(f"{self.name}/services/{key[0]}/{key[1]}/{key[2]}")
            if key in self.DEPARTMENT_MAPPING:
                branded_item = deepcopy(item)
                branded_item["ref"] = self.make_ref(branded_item, key)
                brand, category = self.DEPARTMENT_MAPPING[key]
                branded_item.update(brand)
                self.parse_contacts(branded_item, service)
                self.parse_hours(branded_item, service)
                apply_category(category, branded_item)
                yield branded_item

        data = response.json()
        current_page = data["page"]["number"]
        if current_page < data["page"]["totalPages"]:
            yield self.make_request(country, current_page + 1)

    def parse_contacts(self, item: Feature, service: dict) -> None:
        communication = service.get("communication", {})
        item["website"] = communication.get("INTERNET", "").strip().lower()
        item["email"] = communication.get("EMAIL")
        item["phone"] = communication.get("PHONE")
        if item.get("website") and not item.get("website", "").startswith("http"):
            item["website"] = "https://" + item["website"]

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

    def make_ref(self, item: Feature, key: tuple[str, str, str]) -> str:
        country = item["country"]
        brand, service, product_group = key

        if service.startswith("OMNIplus"):
            # Handle presence of multiple different OMNIplus services at the same location
            # assuming deduplication pipeline is enabled for the spider.
            service = "OMNIplus"
            brand = "OMNIplus"

        return "-".join([item["ref"], country, brand, service, product_group]).replace(" ", "-")
