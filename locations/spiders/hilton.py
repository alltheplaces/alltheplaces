import json

import requests
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import CHROME_LATEST


class HiltonSpider(Spider):
    name = "hilton"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": CHROME_LATEST,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        },
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 2,
    }
    token = None

    # More details about brand codes is in filters section of https://www.hilton.com/en/locations/hilton-hotels/
    BRANDS_MAPPING = {
        "CH": ("Conrad", "Q855525"),
        "DT": ("DoubleTree", "Q2504643"),
        "ES": ("Embassy Suites", "Q5369524"),
        "GI": ("Hilton Garden Inn", "Q1162859"),
        "GU": ("Graduate", "Q85846030"),
        "GV": ("Hilton Grand Vacations", "Q13636126"),
        "HI": ("Hilton", "Q598884"),
        "HP": ("Hampton", "Q5646230"),
        "HT": ("Home2 Suites", "Q5887912"),
        "HW": ("Homewood Suites", "Q5890701"),
        "LX": ("Small Luxury Hotels of the World", None),
        "ND": ("NoMad", None),
        "OL": ("LXR Hotels & Resorts", "Q64605184"),
        "OU": ("AutoCamp", None),
        "PE": ("Spark by Hilton", None),
        "PO": ("Tempo", "Q112144357"),
        "PY": ("Canopy", "Q30632909"),
        "QQ": ("Curio Collection", "Q19903229"),
        "RU": ("Tru", "Q24907770"),
        "SA": ("Signia", "Q112144335"),
        "UA": ("Motto", "Q112144350"),
        "UP": ("Tapestry Collection", "Q109275422"),
        "WA": ("Waldorf Astoria", "Q3239392"),
    }

    # TODO: map more services
    SERVICES_MAPPING = {
        "adjoiningRooms": None,
        "adventureStays": None,
        "airportShuttle": None,
        "allInclusive": None,
        "beach": None,
        "boutique": None,
        "businessCenter": None,
        "casino": None,
        "concierge": None,
        "digitalKey": None,
        "dining": None,
        "evCharging": None,
        "eveningReception": None,
        "executiveLounge": None,
        "fitnessCenter": None,
        "freeBreakfast": None,
        "freeParking": None,
        "freeWifi": Extras.WIFI,
        "golf": None,
        "hotelResidence": None,
        "inRoomKitchen": None,
        "indoorPool": Extras.SWIMMING_POOL,
        "luxury": None,
        "meetingRooms": None,
        "newHotel": None,
        "nonSmoking": "smoking=no",
        "outdoorPool": None,
        "petsAllowed": None,
        "petsNotAllowed": None,
        "resort": None,
        "roomService": None,
        "ski": None,
        "spa": None,
        "streamingTv": None,
        "tennisCourt": None,
    }

    def start_requests(self):
        url = "https://www.hilton.com/dx-customer/auth/applications/token?appName=dx_shop_search_app"
        headers = {
            "x-dtpc": "ignore",
        }
        data = {"app_id": "096a02c6-e844-41b4-bebf-ec74e3ca3cd4"}
        yield JsonRequest(url, headers=headers, data=data, callback=self.parse_token)

    def parse_token(self, response: Response):
        self.token = response.json()["access_token"]
        yield from self.get_quadrants()

    def get_quadrants(self):
        url = "https://www.hilton.com/graphql/customer?appName=dx_shop_search_app&operationName=hotelQuadrants&originalOpName=hotelQuadrants&bl=en"
        data = {
            "query": "query hotelQuadrants {hotelQuadrants{ id } }",
            "operationName": "hotelQuadrants",
            "variables": {},
        }
        yield JsonRequest(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
            },
            data=data,
            callback=self.parse_quadrants,
        )

    def parse_quadrants(self, response: Response):
        quadrants = response.json()["data"]["hotelQuadrants"]
        for quadrant in quadrants:
            yield from self.parse_hotels(quadrant["id"])

    def parse_hotels(self, quadrant_id):
        response = self.get_hotels(quadrant_id)

        for poi in response.json()["data"]["hotelSummaryOptions"]["hotels"]:
            poi.update(poi.pop("address"))
            poi.update(poi.pop("contactInfo"))
            item = DictParser.parse(poi)
            item["ref"] = poi["ctyhocn"]
            item["website"] = poi.get("facilityOverview", {}).get("homeUrlTemplate")
            item["lat"] = poi.get("localization", {}).get("coordinate", {}).get("latitude")
            item["lon"] = poi.get("localization", {}).get("coordinate", {}).get("longitude")

            if brand_code := poi.get("brandCode"):
                if match := self.BRANDS_MAPPING.get(brand_code):
                    item["brand"], item["brand_wikidata"] = match
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{brand_code}")

            for service in poi.get("amenityIds", []):
                if match := self.SERVICES_MAPPING.get(service):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_service/{service}")

            apply_category(Categories.HOTEL, item)
            yield item

    def get_hotels(self, quadrant_id):
        # TODO: we should use JsonRequest here, but it doesn't work with this endpoint for some reason!
        url = "https://www.hilton.com/graphql/customer?appName=dx_shop_search_app&operationName=hotelSummaryOptions&originalOpName=hotelSummaryOptions&bl=en"
        data = {
            "operationName": "hotelSummaryOptions",
            "query": """
                query
                    hotelSummaryOptions($language: String!, $input: HotelSummaryOptionsInput) {
                        hotelSummaryOptions(language: $language, input: $input) {
                            hotels {
                                ctyhocn
                                amenityIds
                                brandCode
                                facilityOverview { allowAdultsOnly homeUrlTemplate }
                                name
                                display { open openDate preOpenMsg resEnabled resEnabledDate treatments }
                                contactInfo { phoneNumber }
                                address { addressLine1 city country countryName state stateName _id }
                                localization { currencyCode coordinate { latitude longitude } }
                                images { master(ratios: [threeByTwo]) { altText ratios { size url } } carousel(ratios: [threeByTwo]) { altText ratios { url size } } } } } }
                    """,
            "variables": {"input": {"guestLocationCountry": "HU", "quadrantId": f"{quadrant_id}"}, "language": "en"},
        }
        headers = {
            "User-Agent": CHROME_LATEST,
            "Content-Type": "application/json",
        }
        return requests.post(url, headers=headers, data=json.dumps(data))
