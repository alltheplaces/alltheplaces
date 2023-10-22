import re

import scrapy

from locations.categories import Categories, Extras, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

# List of brands and countries where they operate:
# https://www.omv.com/en/customers/services/filling-stations
BRANDS_AND_COUNTRIES = {
    "OMV": {
        "countries": ["AUT", "BGR", "HUN", "CZE", "ROU", "SRB", "SVK"],
        "brand": "OMV",
        "brand_wikidata": "Q168238",
    },
    "PETROM": {"countries": ["ROU", "MDA"], "brand": "Petrom", "brand_wikidata": "Q1755034"},
    "AVANTI": {"countries": ["AUT"], "brand": "Avanti", "brand_wikidata": "Q168238"},
    "HOFER": {"countries": ["AUT"], "brand": "Hofer Diskont", "brand_wikidata": "Q107803455"},
}

SITE_FEATURES_MAP = {
    "ATM": Extras.ATM,
    "Car wash hall": Extras.CAR_WASH,
    "CNG": Fuel.CNG,
    # TODO: map high flow pump, this seems an important attribute for petrol stations!
    "High speed pump": None,
    "Hydrogen": Fuel.LH2,
    "LPG": Fuel.LPG,
    "LPG gas cylinder": Fuel.PROPANE,
    "MaxxMotion 100plus": Fuel.OCTANE_100,
    "MaxxMotion 95": Fuel.OCTANE_95,
    "MaxxMotion Diesel": Fuel.DIESEL,
    "Self-service car wash": Extras.CAR_WASH,
    "Vacuum cleaner": Extras.VACUUM_CLEANER,
    "WIFI": Extras.WIFI,
    # TODO: map the following where possible
    "Alzabox": None,
    "Bank service": None,
    "Car care areas": None,
    "Coffee corner": None,
    "Digital Vignette": None,
    "Electric fast charging": None,
    "Geis point": None,
    "HUGO highway toll": None,
    "Medipoint": None,
    "My Auchan": None,
    "Open 24 hours": None,
    "Pay at the pump": None,
    "Postal service": None,
    "Restaurant": None,
    "SMILE & DRIVE": None,
    "Sazka terminal": None,
    "Shop": None,
    "Spar Express": None,
    "Super Shop": None,
    "Tabacco shop": None,
    "Tankomat open 24 hours": None,
    "Ticketportal": None,
    "VIVA shop": None,
    "Vignette": None,
    "Waste oil collection": None,
}

PAYMENT_METHODS_MAP = {
    "American Express Card": PaymentMethods.AMERICAN_EXPRESS,
    "ATM Card": PaymentMethods.CARDS,
    "Diners Club Card": PaymentMethods.DINERS_CLUB,
    "DKV": FuelCards.DKV,
    "Master Card": PaymentMethods.MASTER_CARD,
    "OMV Card": FuelCards.OMV,
    "Routex Card": FuelCards.ROUTEX,
    "UTA": FuelCards.UTA,
    "VISA Card": PaymentMethods.VISA,
    # TODO: find payment methods for the following
    "ARBÖ Card": None,
    "Cadhoc": None,
    "CadouPass": None,
    "CheckDejeuner": None,
    "GustoPass": None,
    "SmartPass": None,
    "TicketRestaurant": None,
    "Westaco": None,
    "jö Karte": None,
    "Lotto Toto acceptence": None,
}


class OmvSpider(scrapy.Spider):
    name = "omv"
    start_urls = ["https://www.omv.at/de-at/tanken/tankstellensuche"]
    download_delay = 0.10
    api_url = "https://app.wigeogis.com/kunden/omv/data/getresults.php"
    details_url = "https://app.wigeogis.com/kunden/omv/data/details.php"

    def parse(self, response):
        javascript_code = response.xpath("//script[contains(., 'var IConfHash')]/text()").get()
        iconf_hash = re.search(r"var IConfHash = '([^']+)'", javascript_code).group(1)
        iconf_ts = re.search(r"var IConfTs = '([^']+)'", javascript_code).group(1)

        for brand, brand_data in BRANDS_AND_COUNTRIES.items():
            for country in brand_data["countries"]:
                yield scrapy.FormRequest(
                    url=self.api_url,
                    formdata={
                        "CTRISO": country,
                        "BRAND": brand,
                        "VEHICLE": "CAR",
                        "MODE": "NEXTDOOR",
                        "ANZ": "1000",
                        "HASH": iconf_hash,
                        "TS": iconf_ts,
                    },
                    callback=self.parse_pois,
                    meta={
                        "country": country,
                        "brand": brand_data["brand"],
                        "brand_wikidata": brand_data["brand_wikidata"],
                        "HASH": iconf_hash,
                        "TS": iconf_ts,
                    },
                )

    def parse_pois(self, response):
        for poi in response.json():
            yield scrapy.FormRequest(
                url=self.details_url,
                formdata={
                    "ID": poi["sid"],
                    "HASH": response.meta["HASH"],
                    "TS": response.meta["TS"],
                },
                callback=self.parse_poi,
                meta=response.meta,
            )

    def parse_poi(self, response):
        data = response.json()
        details = data.get("siteDetails", {})
        item = DictParser.parse(details)
        item["ref"] = details.get("sid")
        item["lat"] = details.get("y_coordinates")
        item["lon"] = details.get("x_coordinates")
        item["street_address"] = details.get("address_l")
        item["city"] = details.get("town_l")
        item["phone"] = details.get("telnr") if details.get("telnr") != "NO TELEPHONE" else None
        item["brand"] = response.meta["brand"]
        item["brand_wikidata"] = response.meta["brand_wikidata"]
        item["country"] = response.meta["country"]
        self.parse_hours(item, details)
        self.parse_attribute(item, data, "siteFeatures", SITE_FEATURES_MAP)
        self.parse_attribute(item, data, "paymentDetails", PAYMENT_METHODS_MAP)
        apply_category(Categories.FUEL_STATION, item)
        # TODO: fuel types are provided as images, parse them somehow. OCR?
        yield item

    def parse_hours(self, item, details):
        """
        Example opening hours string:
            "dayOfWeek=1,closed=FALSE,from=05:00,to=22:00#dayOfWeek=2,closed=FALSE,from=05:00,to=22:00"
        """
        oh = OpeningHours()
        hours = details.get("opening_hours")
        try:
            if hours:
                for day in hours.split("#"):
                    day_of_week, closed, from_time, to_time = day.split(",")
                    day_of_week = day_of_week.split("=")[1]
                    closed = closed.split("=")[1]
                    from_time = from_time.split("=")[1]
                    to_time = to_time.split("=")[1]
                    if closed == "TRUE":
                        continue
                    oh.add_range(DAYS[int(day_of_week) - 1], from_time, to_time)
                item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.error(f"Error parsing hours: {hours}, {e}")

    def parse_attribute(self, item, data: dict, attribute_name: str, mapping: dict):
        for attribute in data.get(attribute_name, []):
            title = attribute.get("title")
            # Some titles have brackets at the end of the string - remove them.
            title = title.split("(")[0].strip()
            if tag := mapping.get(title):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/omv/{attribute_name}/failed/{title}")
