from copy import deepcopy
from typing import Any, AsyncIterator

import reverse_geocoder
from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.volkswagen import VolkswagenSpider


class SkodaSpider(Spider):
    name = "skoda"
    item_attributes = {"brand": "Škoda", "brand_wikidata": "Q29637"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    available_countries_skoda_api = {
        107: ("de-DE", "DE"),
        109: ("en-mu", "MU"),
        202: ("nl-BE", "BE"),
        207: ("el-GR", "GR"),
        210: ("en-gb", "GB"),
        216: ("fr-LU", "LU"),
        217: ("en-mt", "MT"),
        218: ("nb-no", "NO"),
        222: ("sv-se", "SE"),
        223: ("de-ch", "CH"),
        260: ("cs-CZ", "CZ"),
        264: ("it-it", "IT"),
        282: ("es-ic", "ES"),
        285: ("zh-tw", "TW"),
        294: ("en-CY", "CY"),
        296: ("be-by", "BY"),
        308: ("fr-ma", "MA"),
        318: ("en-dz", "DZ"),
        334: ("fr-TN", "TN"),
        352: ("vi-VN", "VN"),
        411: ("lv-LV", "LV"),
        423: ("tr-tr", "TR"),
        428: ("en-sa", "SA"),
        438: ("nl-nl", "NL"),
        442: ("da-dk", "DK"),
        443: ("fi-fi", "FI"),
        451: ("bg-bg", "BG"),
        456: ("pl-pl", "PL"),
        457: ("sr-latn-CS", "RS"),
        462: ("et-ee", "EE"),
        472: ("lt-LT", "LT"),
        572: ("es-es", "ES"),
        622: ("ro-MD", "MD"),
        654: ("sk-SK", "SK"),
        663: ("en-IN", "IN"),
        703: ("en-np", "NP"),
        710: ("en-kw", "KW"),
        715: ("en-BH", "BH"),
        745: ("en-ae", "AE"),
        777: ("en-bn", "BN"),
        824: ("en-nz", "NZ"),
        885: ("en-qa", "QA"),
        886: ("uk-UA", "UA"),
        941: ("en-IE", "IE"),
        959: ("en-AU", "AU"),
        961: ("ru-kz", "KZ"),
        995: ("fr-FR", "FR"),
    }

    available_countries_porsche_api = ["AL", "AT", "BA", "CL", "CO", "HR", "HU", "MK", "PT", "RO", "SG", "SI"]

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        # TODO: check how to get country ids dynamically
        for country_id, country in self.available_countries_skoda_api.items():
            yield JsonRequest(
                url="https://www.skoda-auto.de/apps/retailers/api/{}/{}/DealersV2/GetDealers".format(
                    country_id, country[0]
                ),
                meta={"country": country, "country_id": country_id},
                callback=self.request_details,
            )

        for country in self.available_countries_porsche_api:
            yield Request(
                url=f"https://groupcms-services-api.porsche-holding.com/v3/dealers/{country}/C",
                callback=VolkswagenSpider.parse_porsche_api,
                meta={"brand": self.item_attributes, "country": country, "crawler": self.crawler},
            )

    def request_details(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            yield JsonRequest(
                url="https://www.skoda-auto.de/apps/retailers/api/{}/{}/DealersV2/GetDealerDetail?id={}".format(
                    response.meta["country_id"], response.meta["country"][0], store["globalId"]
                ),
                meta={"country_code": response.meta["country"][1]},
                callback=self.parse_skoda_api,
            )

    def parse_skoda_api(self, response: Response, **kwargs: Any) -> Any:
        store = response.json()
        store.update(store.pop("address", {}))
        item = DictParser.parse(store)
        item["street_address"] = item.pop("street")
        item["ref"] = store["globalId"]
        item["website"] = (store.get("contact") or {}).get("webUrl")
        item["country"] = response.meta["country_code"]

        # Some coordinates in TR have lat and lon switched and are usually bad.
        # Locations in ME have country property equal to RS
        if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
            if item["country"] != result["cc"] and item["country"] == "TR":
                item["lon"] = None
                item["lat"] = None
            elif item["country"] != result["cc"] and item["country"] == "RS":
                item["country"] = result["cc"]

        facilities = [
            facility.get("code", "").lower()
            for department in ["sales", "services"]
            for facility in store.get(department, [])
        ]

        shop_facility = next((f for f in ["sales", "usedcarsales"] if f in facilities), None)
        service_facility = next((f for f in ["service"] if f in facilities), None)

        if shop_facility:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            department = self.extract_department(store, "sale", shop_facility)
            contact = department.get("contact") or {}
            opening_hours = department.get("openingHours") or []
            shop_item["phone"] = contact.get("telephone")
            shop_item["email"] = contact.get("email")
            try:
                shop_item["opening_hours"] = self.parse_hours(opening_hours)
            except Exception as e:
                self.logger.warning("Error parsing hours for {}: {}".format(shop_item["ref"], e))
            apply_category(Categories.SHOP_CAR, shop_item)
            apply_yes_no(Extras.VEHICLE_USED_CAR_SALES, shop_item, "usedcarsales" in facilities)
            yield shop_item

        if service_facility:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            department = self.extract_department(store, "service", service_facility)
            contact = department.get("contact") or {}
            opening_hours = department.get("openingHours") or []
            service_item["phone"] = contact.get("telephone")
            service_item["email"] = contact.get("email")
            try:
                service_item["opening_hours"] = self.parse_hours(opening_hours)
            except Exception as e:
                self.logger.warning("Error parsing hours for {}: {}".format(service_item["ref"], e))
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

    def extract_department(self, store: dict, department: str, facility: str) -> dict | None:
        service = store.get(department) or {}
        departments = service.get("items") or []
        return next(
            (d for d in departments if (d.get("code") or "").lower() == facility),
            None,
        )

    def parse_hours(self, hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for entry in hours:
            day = entry["weekDay"]
            hour_type = entry["openingHourType"]
            if hour_type == "closed":
                oh.set_closed(day)
            elif hour_type in ("oneTimeInterval", "twoTimeIntervals"):
                intervals = ("1",) if hour_type == "oneTimeInterval" else ("1", "2")
                for i in intervals:
                    open_time = entry[f"interval{i}From"]
                    close_time = entry[f"interval{i}To"]
                    oh.add_range(day, open_time, close_time, "%H:%M:%S")
        return oh
