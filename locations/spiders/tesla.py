from typing import AsyncIterator, Dict, Iterable, List

import chompjs
from scrapy import Spider
from scrapy.http import Request, Response
from scrapy_zyte_api.responses import ZyteAPITextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class TeslaSpider(Spider):
    name = "tesla"
    TESLA_ATTRIBUTES = {"brand": "Tesla", "brand_wikidata": "Q478214"}
    TESLA_SUPERCHARGER_ATTRIBUTES = {"brand": "Tesla Supercharger", "brand_wikidata": "Q17089620"}
    requires_proxy = True
    custom_settings = {"DOWNLOAD_TIMEOUT": 60, "USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            "https://www.tesla.com/api/findus/get-locations?country=US&view=map",
            callback=self.parse_json_subrequest,
        )

    def parse_json_subrequest(self, response: Response) -> Iterable[Request]:
        json_data = self.extract_json(response)
        locations = self.select_locations(json_data["data"]["data"])
        for slug, types in list(locations.items())[:100]:
            yield Request(
                url=f"https://www.tesla.com/api/findus/get-location-details?locationSlug={slug}&functionTypes={types}&locale=en_US&isInHkMoTw=false",
                callback=self.parse_location,
            )

    def parse_location(self, response: Response) -> Iterable[Feature]:
        location = self.extract_json(response)
        data = location.get("data", {})
        if data.get("sales_function"):
            yield self.build_store(data)
        if data.get("service_function"):
            yield self.build_service(data)
        if data.get("supercharger_function"):
            yield self.build_supercharger(data)

    def extract_json(self, response: Response) -> dict | List[dict]:
        # For some reason, the scrapy_zyte_api library doesn't detect this as a ScrapyTextResponse, so we have to do the text encoding ourselves.
        # Throws an error when caching is enabled.
        try:
            response = ZyteAPITextResponse.from_api_response(response.raw_api_response, request=response.request)
        except Exception:
            pass
        if json_data := chompjs.parse_js_object(response.text):
            return json_data
        return {}

    def build_store(self, location: dict) -> Feature:
        item = self.build_item(location)
        item.update(self.TESLA_ATTRIBUTES)
        item["website"] = self.parse_url("store", item["ref"])
        item["ref"] = f"{item['ref']}-STORE"
        sales = next((f for f in location["functions"] if f["name"] == "Tesla_Center_Sales"), None)
        if sales:
            item["name"] = sales["customer_facing_name"]
        sales_func = location["sales_function"]
        if email := self.parse_email(sales_func.get("store_email")):
            item["email"] = email
        item["opening_hours"] = self.parse_hours(sales_func.get("business_hours", {}).get("hours", []))
        if not item.get("phone"):
            item["phone"] = location["marketing"]["phone_numbers"]
        apply_category(Categories.SHOP_CAR, item)
        return item

    def build_service(self, location: dict) -> Feature:
        item = self.build_item(location)
        item.update(self.TESLA_ATTRIBUTES)
        service = next((f for f in location["functions"] if f["name"] == "Tesla_Center_Service"), None)
        if service:
            item["name"] = service["customer_facing_name"]
            item["website"] = self.parse_url("service", item["ref"])
        else:
            collision = next((f for f in location["functions"] if f["name"] == "Tesla_Center_Collision"), None)
            if collision:
                item["name"] = collision["customer_facing_name"]
                item["website"] = self.parse_url("bodyshop", item["ref"])
        service_func = location["service_function"]
        if email := self.parse_email(service_func.get("service_center_email")):
            item["email"] = email
        item["opening_hours"] = self.parse_hours(service_func.get("business_hours", {}).get("hours", []))
        if not item.get("phone"):
            item["phone"] = location["marketing"]["service_center_phone"]
        item["ref"] = f"{item['ref']}-SERVICE"
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        return item

    def build_supercharger(self, location: dict) -> Feature:
        item = self.build_item(location)
        item.update(self.TESLA_SUPERCHARGER_ATTRIBUTES)
        item["website"] = self.parse_url("supercharger", item["ref"])
        item["ref"] = f"{item['ref']}-SUPERCHARGER"
        charger_func = location["supercharger_function"]
        output = charger_func["installed_full_power"]
        capacity = charger_func["num_charger_stalls"]
        ccs_compat = charger_func["open_to_non_tesla"]
        if not item.get("phone"):
            item["phone"] = location["marketing"]["roadside_assistance_number"]
        if ccs_compat:
            item["extras"]["socket:type2_combo"] = capacity
            item["extras"]["socket:type2_combo:output"] = output
        else:
            item["extras"]["socket:nacs"] = capacity
            item["extras"]["socket:nacs:output"] = output
        apply_category(Categories.CHARGING_STATION, item)
        return item

    def build_item(self, location: dict) -> Feature:
        feature = DictParser.parse(location["key_data"])
        feature["ref"] = location["marketing"]["location_url_slug"]
        feature["street_address"] = location["key_data"]["address"]["address_1"]
        return feature

    def parse_email(self, email: str) -> str | None:
        # Filter internal distribution list emails (DL-* format)
        if email and not email.startswith("DL-"):
            return email

    def parse_url(self, location_type: str, slug: str) -> str:
        return f"https://www.tesla.com/findus/location/{location_type}/{slug}"

    def parse_hours(self, hours: list[dict]) -> OpeningHours:
        try:
            oh = OpeningHours()
            for entry in hours:
                if entry["is_closed"]:
                    oh.set_closed(entry["day"])
                else:
                    oh.add_range(entry["day"], entry["open_hour"], entry["close_hour"])
            return oh
        except Exception as e:
            self.logger.warning("Error parsing {} {}".format(hours, e))

    # Skip destination chargers as they're not Tesla-operated
    # Skip if "Coming Soon" - no content to capture yet
    # Selection only those in categories list
    # Merge same slugs into one entry, combining types
    def select_locations(self, locations: List[dict]) -> Dict[str, str]:
        categories = {"sales", "service", "bodyshop", "supercharger", "nacs", "party"}
        slug_mapping: dict[str, list[str]] = {}
        for loc in locations:
            if not isinstance(loc, dict):
                continue
            slug = loc.get("location_url_slug")
            loc_types = loc.get("location_type", [])
            if not slug or not categories.intersection(loc_types):
                continue
            slug_mapping.setdefault(slug, []).extend(loc_types)
        return {slug: ",".join(types) for slug, types in slug_mapping.items()}
