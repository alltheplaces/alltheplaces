import re
from html import unescape
from typing import Iterable, List

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Request, Response
from scrapy_zyte_api.responses import ZyteAPITextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class TeslaSpider(Spider):
    name = "tesla"
    TESLA_ATTRIBUTES = {"brand": "Tesla", "brand_wikidata": "Q478214"}
    TESLA_SUPERCHARGER_ATTRIBUTES = {"brand": "Tesla Supercharger", "brand_wikidata": "Q17089620"}
    requires_proxy = True
    download_timeout = 60

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            "https://www.tesla.com/cua-api/tesla-locations?translate=en_US&usetrt=true",
            callback=self.parse_json_subrequest,
        )

    def parse_json_subrequest(self, response: Response) -> Iterable[Request]:
        json_data = self.extract_json(response)
        locations = self.select_locations(json_data)

        for location in locations:
            yield Request(
                url=f"https://www.tesla.com/cua-api/tesla-location?translate=en_US&usetrt=true&id={location.get('location_id')}",
                callback=self.parse_location,
            )

    def parse_location(self, response: Response) -> Iterable[Feature]:
        location = self.extract_json(response)
        location_types: List[str] = location.get("location_type", [])

        if "store" in location_types:
            yield self.build_store(location)

        if any(i in location_types for i in ["service", "bodyshop"]):
            yield self.build_service(location)

        if "supercharger" in location_types:
            yield self.build_supercharger(location)

    def extract_json(self, response: Response) -> dict | List[dict]:
        # For some reason, the scrapy_zyte_api library doesn't detect this as a ScrapyTextResponse, so we have to do the text encoding ourselves.
        response = ZyteAPITextResponse.from_api_response(response.raw_api_response, request=response.request)
        if json_data := chompjs.parse_js_object(response.text):
            return json_data
        return {}

    def build_store(self, location: dict) -> Feature:
        item = self.build_item(location)
        item["ref"] = f"{item['ref']}-STORE"
        item["brand"] = self.TESLA_ATTRIBUTES["brand"]
        item["brand_wikidata"] = self.TESLA_ATTRIBUTES["brand_wikidata"]
        item["website"] = self.parse_url("store", location)
        item["phone"] = self.parse_phone("store", location)
        item["opening_hours"] = self.parse_hours(location.get("store_hours"))
        apply_category(Categories.SHOP_CAR, item)
        return item

    def build_service(self, location: dict) -> Feature:
        item = self.build_item(location)
        item["ref"] = f"{item['ref']}-SERVICE"
        item["brand"] = self.TESLA_ATTRIBUTES["brand"]
        item["brand_wikidata"] = self.TESLA_ATTRIBUTES["brand_wikidata"]
        if "service" in location.get("location_type", []):
            item["website"] = self.parse_url("service", location)
        else:
            item["website"] = self.parse_url("bodyshop", location)
        # some bodyshop locations have only service-phone
        # meanwhile others - only bodyshop-phone
        if phone := self.parse_phone("service", location):
            item["phone"] = phone
        else:
            item["phone"] = self.parse_phone("bodyshop", location)

        item["opening_hours"] = self.parse_hours(location.get("service_hours"))
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        return item

    def build_supercharger(self, location: dict) -> Feature:
        item = self.build_item(location)
        item["ref"] = f"{item['ref']}-SUPERCHARGER"
        item["brand"] = self.TESLA_SUPERCHARGER_ATTRIBUTES["brand"]
        item["brand_wikidata"] = self.TESLA_SUPERCHARGER_ATTRIBUTES["brand_wikidata"]
        item["website"] = self.parse_url("supercharger", location)
        item["phone"] = self.parse_phone("roadside", location)
        regex = r"(\d+) Superchargers, available 24\/7, up to (\d+kW)(<br />CCS Compatibility)?"
        regex_matches = re.findall(regex, location.get("chargers"))
        if regex_matches:
            for match in regex_matches:
                capacity, output, ccs_compat = match
                if ccs_compat:
                    item["extras"]["socket:type2_combo"] = capacity
                    item["extras"]["socket:type2_combo:output"] = output
                else:
                    item["extras"]["socket:nacs"] = capacity
                    item["extras"]["socket:nacs:output"] = output
        apply_category(Categories.CHARGING_STATION, item)
        return item

    def build_item(self, location: dict) -> Feature:
        feature = DictParser.parse(location)
        feature["ref"] = location.get("location_id")
        if street_address := location.get("address_line_1"):
            feature["street_address"] = street_address.replace("<br />", ", ")
        feature["state"] = location.get("province_state")
        # Deal with https://github.com/alltheplaces/alltheplaces/issues/10892
        feature_email = feature.get("email")
        if feature_email and isinstance(feature_email, dict) and "value" in feature_email:
            feature["email"] = feature_email["value"]
        return feature

    def parse_phone(self, location_type: str, location: dict) -> str | None:
        phones = location.get("sales_phone")
        if not isinstance(phones, list):
            return None
        return next((phone.get("number") for phone in phones if phone.get("type") == location_type), None)

    def parse_url(self, location_type: str, location: dict) -> str:
        return f"https://www.tesla.com/findus/location/{location_type}/{location.get('location_id')}".replace(" ", "")

    def parse_hours(self, hours: str) -> OpeningHours:
        oh = OpeningHours()
        clean_html = unescape(hours)
        rows = Selector(text=clean_html).xpath("//table/tr")
        for row in rows:
            day = row.xpath("td[1]/text()").get()
            hours = row.xpath("td[2]/text()").get()
            oh.add_ranges_from_string(f"{day}: {hours}")
        return oh

    # Skip destination chargers as they're not Tesla-operated
    # Skip if "Coming Soon" - no content to capture yet
    # Selection only those in categories list
    def select_locations(self, locations: List[dict]) -> List[dict]:
        categories = ["store", "service", "bodyshop", "supercharger"]
        return list(
            filter(
                lambda location: location.get("open_soon") != "1"
                and "destination charger" not in location.get("location_type", [])
                and any(category in location.get("location_type", []) for category in categories),
                locations,
            )
        )
