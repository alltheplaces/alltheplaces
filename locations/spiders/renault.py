from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class RenaultSpider(Spider):
    name = "renault"

    PAGE_SIZE = 100

    BRANDS = {
        "renault": {"brand": "Renault", "brand_wikidata": "Q6686"},
        "dacia": {"brand": "Dacia", "brand_wikidata": "Q27460"},
        "alpine": {"brand": "Alpine", "brand_wikidata": "Q26944"},
    }

    def make_request(self, host: str, page: int = 0) -> Request:
        return JsonRequest(urljoin(host, "/wired/commerce/v1/dealers?page={}&pageSize={}".format(page, self.PAGE_SIZE)))

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request("https://www.renault.nl/")
        yield self.make_request("https://www.dacia.fr/")
        yield self.make_request("https://www.alpinecars.de/")

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

            if "01" in activities:
                apply_category(Categories.SHOP_CAR, item)
            else:
                apply_category(Categories.SHOP_CAR_REPAIR, item)

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
                    i = item.deepcopy()
                    i["ref"] = "{}-{}".format(item["ref"], key)
                    i.update(brand)
                    yield i

        if response.json()["currentPage"] < response.json()["totalPages"]:
            yield self.make_request(response.url, response.json()["currentPage"] + 1)
