import re
from time import time
from urllib.parse import urlencode

import scrapy

from locations.categories import Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OrlenSpider(scrapy.Spider):
    name = "orlen"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    brand_mappings = {
        "ORLEN": {"brand": "Orlen", "brand_wikidata": "Q971649"},
        "BLISKA": {"brand": "Bliska", "brand_wikidata": "Q4016378"},
        "CPN": {"brand": "CPN"},
        "Petrochemia": {"brand": "Petrochemia"},
        "Benzina": {"brand": "Benzina", "brand_wikidata": "Q11130894"},
        "Ventus": {"brand": "Ventus"},
        "Star": {"brand": "star", "brand_wikidata": "Q109930371"},
    }

    session_id = None

    # https://www.orlen.pl/en/for-you/fuel-stations
    def build_url_params(self, **kwargs):
        session_id_dict = {}
        if self.session_id is not None:
            session_id_dict["sessionId"] = self.session_id
        return urlencode(
            {
                "key": "DC30EA3C-D0D0-4D4C-B75E-A477BA236ACA",  # hardcoded into the page
                "_": int(time() * 1000),
                "format": "json",
            }
            | kwargs
            | session_id_dict
        )

    def start_requests(self):
        yield scrapy.http.JsonRequest(
            "https://wsp.orlen.pl/plugin/GasStations.svc/GetPluginBaseConfig?" + self.build_url_params(),
            callback=self.parse_config,
        )

    def parse_config(self, response):
        self.session_id = response.json()["SessionId"]
        yield scrapy.http.JsonRequest(
            "https://wsp.orlen.pl/plugin/GasStations.svc/FindPOI?"
            + self.build_url_params(
                languageCode="EN",
                gasStationType="",
                services="",
                tags="",
                polyline="",
                keyWords="",
                food="",
                cards="",
                topN="100",
                automaticallyIncreaseDistanceRadius="true",
            ),
        )

    def parse(self, response):
        for location in response.json()["Results"]:
            yield scrapy.http.JsonRequest(
                "https://wsp.orlen.pl/plugin/GasStations.svc/GetGasStation?"
                + self.build_url_params(
                    languageCode="EN",
                    gasStationId=location["Id"],
                    gasStationTemplate="DlaKierowcowTemplates",  # "for drivers template"
                ),
                callback=self.parse_location,
            )

    def parse_location(self, response):
        data = response.json()
        item = DictParser.parse(data)
        if brand := self.brand_mappings.get(data["BrandTypeName"]):
            item.update(brand)
        item.pop("street_address")
        item["street"] = data["StreetAddress"]
        if item["phone"] == "---":
            item["phone"] = None
        if data["BrandTypeName"].lower() not in data["Name"].lower():
            item["name"] = data["BrandTypeName"] + " " + data["Name"]

        facility_names = [facility["Value"] for facility in data["Facilities"]]

        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Changing table for babies" in facility_names)
        apply_yes_no(Extras.TOILETS, item, "TOILETS" in facility_names)
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "Toilet for handicap people" in facility_names)
        apply_yes_no(Extras.WHEELCHAIR, item, "Handicap accessible entrance" in facility_names)
        apply_yes_no(Extras.WIFI, item, "WIFI" in facility_names)
        apply_yes_no(Extras.CAR_WASH, item, "No-touch wash" in facility_names)
        apply_yes_no(Extras.CAR_WASH, item, "Automatic wash" in facility_names)
        apply_yes_no(Extras.SHOWERS, item, "Shower" in facility_names)

        gas_names = [gas["Value"] for gas in data["Gas"]]
        apply_yes_no(Fuel.DIESEL, item, "EFECTA DIESEL" in gas_names)
        apply_yes_no(Fuel.DIESEL, item, "Verva ON" in gas_names)  # ON = olej napędowy = "propulsion oil" = diesel
        apply_yes_no(Fuel.LPG, item, "LPG GAS" in gas_names)
        apply_yes_no(Fuel.OCTANE_95, item, "EFECTA 95" in gas_names)
        apply_yes_no(Fuel.OCTANE_98, item, "Verva 98" in gas_names)
        apply_yes_no(Fuel.ADBLUE, item, "ADBLUE from the distributor" in gas_names)
        apply_yes_no(Fuel.HGV_DIESEL, item, "ON TIR" in gas_names)

        services_names = [service["Value"] for service in data["Services"]]
        apply_yes_no(Extras.COMPRESSED_AIR, item, "Compressor" in services_names)
        apply_yes_no(Extras.ATM, item, "Cash point" in services_names)

        # TODO: output separate item for charging station
        if "Electric car chargers" in services_names:
            apply_category(Categories.CHARGING_STATION, item)

        cards_names = [card["Value"] for card in data["Cards"]]
        apply_yes_no(FuelCards.LOGPAY, item, "LogPay" in cards_names)
        apply_yes_no(FuelCards.DKV, item, "DKV" in cards_names)
        apply_yes_no(FuelCards.UTA, item, "UTA" in cards_names)

        is_24h = (
            data["OpeningHours"]
            in [
                "Całodobowo",
            ]
            or "Open 24h" in facility_names
        )

        if is_24h:
            item["opening_hours"] = "24/7"
        else:
            # parse "7 dni 06-22"
            match = re.search(r"7 dni (\d+)-(\d+)", data["OpeningHours"])
            if match:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, match.group(1) + ":00", match.group(2) + ":00")

        if len(gas_names) > 0 or len(cards_names) == 0:
            # note that some listed locations are not providing any fuel
            # but also, some places are not having any detail provided at all
            # in such cases lets assume that these are fuel stations
            apply_category(Categories.FUEL_STATION, item)
        yield item
