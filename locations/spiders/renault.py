from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class RenaultSpider(Spider):
    name = "renault"

    PAGE_SIZE = 100

    BRANDS = {
        "renault": {"brand": "Renault", "brand_wikidata": "Q6686"},
        "dacia": {"brand": "Dacia", "brand_wikidata": "Q27460"},
        "alpine": {"brand": "Alpine", "brand_wikidata": "Q26944"},
    }

    def make_request(self, host: str, page: int = 0) -> JsonRequest:
        return JsonRequest(urljoin(host, "/wired/commerce/v1/dealers?page={}&pageSize={}".format(page, self.PAGE_SIZE)))

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request("https://www.renault.nl/")
        yield self.make_request("https://www.dacia.fr/")
        yield self.make_request("https://www.alpinecars.de/")
        yield self.make_request("https://www.renault.co.in/")
        yield self.make_request("https://www.renault.com.br/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            if not location["active"] or location["blacklisted"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["dealerId"]
            item["lat"] = location.get("geolocalization", {}).get("lat")
            item["lon"] = location.get("geolocalization", {}).get("lon")
            item["street_address"] = location["extendedAddress"] or location["streetAddress"]
            item["country"] = location.get("country")
            item["phone"] = location["telephone"].get("value")

            activities = [activity["birId"] for activity in location["dealerActivities"]]

            apply_yes_no("second_hand", item, "03" in activities)
            apply_yes_no("service:vehicle:car_parts", item, "10" in activities)
            apply_yes_no("service:vehicle:mot", item, "17" in activities)

            # TODO?
            # 00 "Main Service"
            # 02 "Renault Business Center"
            # 04 "Mechanical Workshop"
            # 06 "Renault Assistance"
            # 07 "Renault Minute Service"
            # 09 "Pro+ Center"
            # 11 "Renault Boutique"
            # 12 "Renault Rent"
            # 13 "Renault Finance"
            # 14 "Renault Sport"
            # 16 "Leasing"
            # 18 "Electric vehicle sales"
            # 19 "New Vehicle Delivery"
            # 20 "Courtesy Vehicle"
            # 21 "After Sales E.V."
            # 25 "E-commerce"
            # 56 "Renault Mobility"
            # 70 "E-Commerce"
            # 72 "Dacia Corner"
            # 89 "Renault Selection"
            # 278 "Renew Occasions Renault"
            # 359 "Borne de Recharge 24/7"
            # location["type"]
            # location["dealerNature"]

            for key, brand in self.BRANDS.items():
                if location.get(key) and not location[key]["blacklisted"]:
                    is_dealer = "01" in activities
                    is_service = "04" in activities
                    if is_dealer:
                        yield self.create_shop_item(item, key, brand, is_service)
                    if is_service:
                        yield self.create_service_item(item, key, brand)

        if response.json()["currentPage"] < response.json()["totalPages"]:
            yield self.make_request(response.url, response.json()["currentPage"] + 1)

    def create_shop_item(self, item: Feature, key: str, brand: dict, has_service: bool) -> Feature:
        shop = item.deepcopy()
        shop["ref"] = "{}-{}".format(item["ref"], key)
        shop.update(brand)
        apply_category(Categories.SHOP_CAR, shop)
        apply_yes_no(Extras.CAR_REPAIR, shop, has_service)
        return shop

    def create_service_item(self, item: Feature, key: str, brand: dict) -> Feature:
        service = item.deepcopy()
        service["ref"] = "{}-{}_service".format(item["ref"], key)
        service.update(brand)
        apply_category(Categories.SHOP_CAR_REPAIR, service)
        return service
