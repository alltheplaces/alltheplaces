from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature


class MaesMobilityBENLSpider(scrapy.Spider):
    name = "maes_mobility_be_nl"
    item_attributes = {"operator": "Maes"}
    allowed_domains = ["www.maesmobility.be"]

    # Brand to Wikidata mapping
    BRAND_MAPPING = {
        "MAES": {"brand": "Maes"},
        "MAES TRUCK": {"brand": "Maes Truck"},
        "ESSO": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "ESSO EXPRESS": {"brand": "Esso Express", "brand_wikidata": "Q2350336"},
        "SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "SHELL EXPRESS": {"brand": "Shell Express", "brand_wikidata": "Q2289188"},
        "BP": {"brand": "BP", "brand_wikidata": "Q152057"},
        "TOTAL": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
        "Q8": {"brand": "Q8", "brand_wikidata": "Q4119207"},
        "TEXACO": {"brand": "Texaco", "brand_wikidata": "Q775060"},
        "PITPOINT": {"brand": "PitPoint", "brand_wikidata": "Q109923423"},
        "FIREZONE": {"brand": "Firezone", "brand_wikidata": "Q14628080"},
        "G&V": {"brand": "G&V"},
        "G&V TRUCK": {"brand": "G&V Truck"},
        "G&V EXPRESS": {"brand": "G&V Express"},
        "OCTA+": {"brand": "Octa+", "brand_wikidata": "Q2179978"},
        "BRUNO": {"brand": "Bruno"},
        "PMO": {"brand": "PMO"},
        "HAAN": {"brand": "Haan", "brand_wikidata": "Q92553521"},
        "ENORA": {"brand": "Enora"},
        "VISSERS": {"brand": "Vissers", "brand_wikidata": "Q124253846"},
        "AUTOFOOD": {"brand": "Autofood"},
        # Rebranded on 2 June 2025 from International Diesel Services to Q8Truck: https://www.q8truck.com/en/news/ids-becomes-q8truck
        "IDS": {"brand": "Q8Truck", "brand_wikidata": "Q125462248"},
        "GULF": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
        "PUMPY": {"brand": "Pumpy"},
    }

    # Payment method mapping
    PAYMENT_METHOD_MAPPING = {
        "CASH": PaymentMethods.CASH,
        "BANCONTACT": PaymentMethods.BANCONTACT,
        "MAESTRO": PaymentMethods.MAESTRO,
        "MASTERCARD": PaymentMethods.MASTER_CARD,
        "VISA CARD": PaymentMethods.VISA,
        "AMEX": PaymentMethods.AMERICAN_EXPRESS,
        "VPAY": PaymentMethods.V_PAY,
        "CARFOOD": PaymentMethods.CARFOOD,
        "BRUNO": PaymentMethods.BRUNO,
        "CAPS": PaymentMethods.CAPS,
        "HAAN CARD": PaymentMethods.HAAN_CARD,
        "DIESEL CARD": PaymentMethods.DIESEL_CARD,
        "MAES APP": PaymentMethods.MAES_APP,
        "FLEETPASS": PaymentMethods.FLEETPASS,
        "GO EASY WAY": PaymentMethods.GO_EASY_WAY,
        "MAES": PaymentMethods.MAES,
        "XXIMO": PaymentMethods.XXIMO,
        "OCTA+": PaymentMethods.OCTA_PLUS,
        "MAES EUROPE CARD": PaymentMethods.MAES_EUROPE_CARD,
        "MAES PREPAID": PaymentMethods.MAES_PREPAID,
        "KUSTERS": PaymentMethods.KUSTERS,
        "SMART REPORTING": PaymentMethods.SMART_REPORTING,
        "TANX": PaymentMethods.TANX,
        "EG": PaymentMethods.EG,
        "TRAVELCARD": PaymentMethods.TRAVELCARD,
        "MAES HYBRID CARD": PaymentMethods.MAES_HYBRID_CARD,
        "VAB": PaymentMethods.VAB,
    }

    # Fuel card mapping
    FUEL_CARD_MAPPING = {
        "DKV": FuelCards.DKV,
        "UTA": FuelCards.UTA,
        "SHELL CARD": FuelCards.SHELL,
        "ESSO CARD": FuelCards.ESSO_NATIONAL,
        "BP VISSERS": FuelCards.BP,
        "ROUTEX": FuelCards.ROUTEX,
        "EUROWAG": FuelCards.EUROWAG,
        "LOGPAY": FuelCards.LOGPAY,
        "LUKOIL": FuelCards.LUKOIL,
        "E100": FuelCards.E100,
    }

    # Fuel type mapping (keywords to fuel types)
    FUEL_TYPE_MAPPING = {
        "DIESEL": Fuel.DIESEL,
        "E10": Fuel.E10,
        "E5": Fuel.E5,
        "E85": Fuel.E85,
        "LPG": Fuel.LPG,
        "CNG": Fuel.CNG,
        "LNG": Fuel.LNG,
        "ADBLUE": Fuel.ADBLUE,
    }

    async def start(self):
        # Single API call with bounds covering all of Belgium and Netherlands
        yield JsonRequest(
            url="https://www.maesmobility.be/api/filter-stations",
            method="POST",
            data={
                "fuelTypes": [],
                "networks": [],
                "paymentMethods": [],
                "carwash": False,
                "shop": False,
                "bounds": {
                    "ne": {"lat": 55.816686773322274, "lng": 10.286890351562516},
                    "sw": {"lat": 47.20833949858102, "lng": -3.8854729296874835},
                    "center": {"latitude": 51.716787802978565, "longitude": 3.2007087109375165},
                },
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()

        for station in data:
            # Build detail page URL from slug
            slug = station.get("slug")
            if slug:
                detail_url = f"https://www.maesmobility.be/nl/tankstation/{slug}/"
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_station_detail,
                    meta={"station": station},
                )

    def parse_station_detail(self, response: Response) -> Iterable[Feature]:
        station = response.meta["station"]
        item = Feature()

        self.populate_basic_fields(item, station, response.url)
        self.apply_brand_info(item, station["title"])
        apply_category(Categories.FUEL_STATION, item)
        self.apply_fuel_types(item, response)
        self.apply_facilities(item, station)
        self.apply_payment_methods(item, station)

        yield item

    def populate_basic_fields(self, item: Feature, station: dict, website_url: str):
        item["ref"] = str(station["id"])
        item["lat"] = station["lat"]
        item["lon"] = station["long"]
        item["street"] = station.get("street")
        item["housenumber"] = station.get("nr")
        item["city"] = station.get("city")
        item["postcode"] = station.get("postalcode")
        item["country"] = self.normalize_country(station)
        item["phone"] = station.get("phone")
        item["website"] = website_url
        item["name"] = station.get("title", "").strip()

    def apply_brand_info(self, item: Feature, title: str):
        """Extract and apply brand information from station title."""
        brand_info = self.extract_brand(title)
        if brand_info:
            item.update(brand_info)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_brand/{title.split()[-1]}")

    def apply_fuel_types(self, item: Feature, response: Response):
        fuel_headings = response.xpath("//h4/text()").getall()
        for fuel_text in fuel_headings:
            fuel_text_upper = fuel_text.upper()
            for keyword, fuel_type in self.FUEL_TYPE_MAPPING.items():
                if keyword in fuel_text_upper:
                    apply_yes_no(fuel_type, item, True)

    def apply_facilities(self, item: Feature, station: dict):
        if station.get("carwash"):
            apply_yes_no(Extras.CAR_WASH, item, True)
        if station.get("shop"):
            apply_yes_no("shop", item, True)

    def apply_payment_methods(self, item: Feature, station: dict):
        payment_methods = station.get("payment_methods", [])
        for pm in payment_methods:
            if pm_tag := self.PAYMENT_METHOD_MAPPING.get(pm):
                apply_yes_no(pm_tag, item, True)
            elif pm_tag := self.FUEL_CARD_MAPPING.get(pm):
                apply_yes_no(pm_tag, item, True)

    def extract_brand(self, title: str) -> dict | None:
        """Extract brand information from station title by finding the longest matching brand name."""
        title_upper = title.upper()

        # Find all brand names that appear in the title
        matching_brands = []
        for brand_name, brand_info in self.BRAND_MAPPING.items():
            if brand_name in title_upper:
                matching_brands.append((brand_name, brand_info))

        # Return the longest match (favors "ESSO EXPRESS" over "ESSO")
        if matching_brands:
            longest_match = max(matching_brands, key=lambda x: len(x[0]))
            return longest_match[1]

        return None

    def normalize_country(self, station: dict) -> str:
        if not station.get("postalcode").isalnum():
            return "NL"

        country = station.get("country")
        if not country:
            return "BE"

        country_upper = country.upper()
        # Handle various spellings
        if "BELGI" in country_upper:
            return "BE"
        elif "NEDERLAND" in country_upper:
            return "NL"
        elif "LUXEMBURG" in country_upper:
            return "LU"

        return "BE"  # Default to Belgium
