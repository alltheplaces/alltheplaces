from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.react_server_components import parse_rsc

LOCATOR_NL = "https://www.qteam.be/nl/onze-service-centers"
LOCATOR_FR = "https://www.qteam.be/fr/nos-centres-de-service"

SERVICES = {
    "wheelAlignment": Extras.VEHICLE_WHEEL_ALIGNMENT_SERVICES,
    "batteries": Extras.VEHICLE_BATTERY_SERVICES,
    "brakes": Extras.VEHICLE_BRAKE_SERVICES,
    "oil": Extras.VEHICLE_OIL_CHANGE_SERVICES,
    "shockAbsorbers": Extras.VEHICLE_SUSPENSION_SERVICES,
}


class QTeamBESpider(Spider):
    name = "q_team_be"
    item_attributes = {"brand": "QTeam", "brand_wikidata": "Q127691554"}
    allowed_domains = ["www.qteam.be"]
    start_urls = [LOCATOR_NL]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(chunk for _, chunk in [chompjs.parse_js_object(script) for script in scripts]).encode()
        garages = next(
            garages
            for garages in DictParser.iter_matching_keys(dict(parse_rsc(rsc)), "garages")
            if isinstance(garages, list)
        )

        def resolve(value: dict | str) -> dict:
            # Repeated objects are replaced with references such as "$25:props:garages:0:services:1".
            if isinstance(value, str):
                target = garages
                for key in value.split(":")[3:]:
                    target = target[int(key) if key.isdigit() else key]
                return resolve(target)
            return value

        for garage in garages:
            if garage["segment"] == "FLEET_PARTNER":
                continue

            item = Feature()
            item["ref"] = garage["externalId"]
            item["lat"] = garage["location"]["lat"]
            item["lon"] = garage["location"]["lng"]
            item["branch"] = garage["title"].removeprefix("QTeam").strip(" -")
            item["addr_full"] = merge_address_lines([garage["addressLine1"], garage["addressLine2"]])
            item["country"] = "BE"
            item["phone"] = garage["phone"]
            item["website"] = item["extras"]["website:nl"] = response.urljoin(garage["url"])
            item["extras"]["website:fr"] = item["website"].replace(LOCATOR_NL, LOCATOR_FR)

            item["opening_hours"] = OpeningHours()
            for rule in garage["openingHours"]:
                if rule["slots"]:
                    for slot in rule["slots"]:
                        item["opening_hours"].add_range(rule["day"], slot["open"], slot["close"])
                else:
                    item["opening_hours"].set_closed(rule["day"])

            apply_category(Categories.SHOP_TYRES, item)
            services = {resolve(service)["id"] for service in garage["services"]}
            vehicles = {resolve(vehicle)["id"] for vehicle in garage["vehicleTypes"]}
            apply_yes_no("car:tyres", item, "van" in vehicles)
            apply_yes_no(Extras.VEHICLE_TYRE_SERVICES, item, "van" in vehicles)
            apply_yes_no("truck:tyres", item, "truck" in vehicles)
            for key, service in SERVICES.items():
                apply_yes_no(service, item, key in services)

            yield item
