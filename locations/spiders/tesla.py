from copy import deepcopy
from typing import List

import chompjs
import scrapy
from scrapy_zyte_api.responses import ZyteAPITextResponse
from html import unescape


from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class TeslaSpider(scrapy.Spider):
    name = "tesla"
    item_attributes = {"brand": "Tesla", "brand_wikidata": "Q478214"}
    requires_proxy = True
    download_timeout = 60
    categories = ["store", "service", "bodyshop"]

    def start_requests(self):
        yield scrapy.Request(
            "https://www.tesla.com/cua-api/tesla-locations?translate=en_US&usetrt=true",
            callback=self.parse_json_subrequest,
        )

    def parse_json_subrequest(self, response):
        # For some reason, the scrapy_zyte_api library doesn't detect this as a ScrapyTextResponse, so we have to do the text encoding ourselves.
        response = ZyteAPITextResponse.from_api_response(response.raw_api_response, request=response.request)
        locations = chompjs.parse_js_object(response.text)
        locations = self.select_locations(locations)

        for location in locations:
            yield scrapy.Request(
                url=f"https://www.tesla.com/cua-api/tesla-location?translate=en_US&usetrt=true&id={location.get('location_id')}",
                callback=self.parse_location,
            )



    def parse_location(self, response):
        # For some reason, the scrapy_zyte_api library doesn't detect this as a ScrapyTextResponse, so we have to do the text encoding ourselves.
        response = ZyteAPITextResponse.from_api_response(response.raw_api_response, request=response.request)

        # Many responses have false error message appended to the json data, clean them to get a proper json
        location_data = chompjs.parse_js_object(response.text)
        if isinstance(location_data, list):
            return
        
        feature = self.build_item(location_data)

        if "store" in location_data.get("location_type"):
            item = deepcopy(feature)
            item["website"] = f"https://www.tesla.com/findus/location/store/{location_data.get('location_id')}".replace(" ", "")
            item["opening_hours"] = self.parse_hours(location_data.get("store_hours"))
            apply_category(Categories.SHOP_CAR, item)
            yield item

        if "service" in location_data.get("location_type") or "bodyshop" in location_data.get("location_type"):
            item = deepcopy(feature)
            item["ref"] = f"{feature['ref']}-SERVICE"
            
            if "service" in location_data.get("location_type"):
                item["website"] = f"https://www.tesla.com/findus/location/service/{location_data.get('location_id')}"
            else:
                item["website"] = f"https://www.tesla.com/findus/location/bodyshop/{location_data.get('location_id')}"

            item["opening_hours"] = self.parse_hours(location_data.get("service_hours"))
            item["website"] = item["website"].replace(" ", "")


            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item


    def build_item(self, location: dict) -> Feature:
        feature = DictParser.parse(location)
        feature["ref"] = location.get("location_id")
        if street_address:=location.get("address_line_1"):
            feature["street_address"] = street_address.replace("<br />", ", ")
        feature["state"] = location.get("province_state")

        # Deal with https://github.com/alltheplaces/alltheplaces/issues/10892
        feature_email = feature.get("email")
        if feature_email and isinstance(feature_email, dict) and "value" in feature_email:
            feature["email"] = feature_email["value"]

        phones = location.get("sales_phone")
        if phones and isinstance(phones, list) and len(phones) > 0:
            feature["phone"] = phones[0]["number"]

        return feature


    def parse_hours(self, hours: str) -> OpeningHours:
        oh = OpeningHours()
        clean_html = unescape(hours)
        rows = scrapy.Selector(text=clean_html).xpath('//table/tr')
        for row in rows:
            day = row.xpath('td[1]/text()').get()
            hours = row.xpath('td[2]/text()').get()
            oh.add_ranges_from_string(f"{day}: {hours}")

        return oh



    # Skip destination chargers as they're not Tesla-operated
    # Skip if "Coming Soon" - no content to capture yet
    # Selection only those in categories list
    def select_locations(self, locations: List[dict]) -> List[dict]:
        return list(filter(lambda location:
            location.get("open_soon") != 1
            and "destination charger" not in location.get("location_type", [])
            and any(category in location.get("location_type", []) for category in self.categories),
            locations
        ))