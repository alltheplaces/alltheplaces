import json
from typing import Any

import requests
from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import CHROME_LATEST


class HiltonSpider(Spider):
    name = "hilton"
    start_urls = ["https://www.hilton.com/en/locations/hilton-hotels/"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": CHROME_LATEST,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        },
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
        "RETRY_TIMES": 5,
    }
    token = None
    requires_proxy = "US"

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
        "OL": ("LXR", "Q64605184"),
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

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for countries in DictParser.iter_matching_keys(
            parse_js_object(response.xpath('//script[contains(text(), "locationPageUri")]/text()').get()), "countries"
        ):
            for country in countries:
                regions = country.get("states") or country.get("cities")
                for region in regions:
                    response = self.get_hotels(region["locationPageUri"])

                    for poi in response.json()["data"]["geocodePage"]["hotelSummaryOptions"]["hotels"]:
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

    def get_hotels(self, location_url: str):
        # TODO: we should use JsonRequest here, but it doesn't work with this endpoint for some reason!
        url = "https://www.hilton.com/graphql/customer?appName=dx_shop_search_app&operationName=hotelSummaryOptions_geocodePage&originalOpName=hotelSummaryOptions_geocodePage&bl=en"

        payload = json.dumps(
            {
                "query": 'query hotelSummaryOptions_geocodePage($language: String!, $path: String!, $queryLimit: Int!, $currencyCode: String!, $distanceUnit: HotelDistanceUnit, $titleFormat: MarkdownFormatType!, $input: HotelSummaryOptionsInput) {\n  geocodePage(language: $language, path: $path) {\n    location {\n      pageInterlinks {\n        title\n        links {\n          name\n          uri\n        }\n      }\n      title(format: $titleFormat)\n      accessibilityTitle\n      meta {\n        pageTitle\n        description\n      }\n      name\n      brandCode\n      category\n      uri\n      globalBounds\n      breadcrumbs {\n        uri\n        name\n      }\n      about {\n        contentBlocks {\n          title(format: text)\n          descriptions\n          orderedList\n          unorderedList\n        }\n        contentBlocks_noTx: contentBlocks {\n          title(format: text)\n          descriptions\n          orderedList\n          unorderedList\n        }\n        isContentLocalized\n      }\n      paths {\n        base\n      }\n      hotelSummaryExtractUrl\n    }\n    match {\n      address {\n        city\n        country\n        countryName\n        state\n        stateName\n      }\n      geometry {\n        location {\n          latitude\n          longitude\n        }\n        bounds {\n          northeast {\n            latitude\n            longitude\n          }\n          southwest {\n            latitude\n            longitude\n          }\n        }\n      }\n      id\n      name\n      type\n    }\n    hotelSummaryOptions(\n      distanceUnit: $distanceUnit\n      sortBy: distance\n      input: $input\n    ) {\n      _hotels {\n        totalSize\n      }\n      bounds {\n        northeast {\n          latitude\n          longitude\n        }\n        southwest {\n          latitude\n          longitude\n        }\n      }\n      amenities {\n        id\n        name\n        hint\n      }\n      amenityCategories {\n        name\n        id\n        amenityIds\n      }\n      brands {\n        code\n        name\n      }\n      hotels(first: $queryLimit) {\n        amenityIds\n        brandCode\n        ctyhocn\n        distance\n        distanceFmt\n        facilityOverview {\n          allowAdultsOnly\n          homeUrlTemplate\n        }\n        name\n        contactInfo {\n          phoneNumber\n        }\n        display {\n          open\n          openDate\n          preOpenMsg\n          resEnabled\n          resEnabledDate\n          treatments\n        }\n        disclaimers {\n          desc\n          type\n        }\n        address {\n          addressFmt\n          addressLine1\n          city\n          country\n          countryName\n          postalCode\n          state\n          stateName\n        }\n        localization {\n          currencyCode\n          coordinate {\n            latitude\n            longitude\n          }\n        }\n        images {\n          master(ratios: [threeByTwo]) {\n            altText\n            ratios {\n              size\n              url\n            }\n          }\n          carousel(ratios: [threeByTwo]) {\n            altText\n            ratios {\n              url\n              size\n            }\n          }\n        }\n        leadRate {\n          lowest {\n            cmaTotalPriceIndicator\n            feeTransparencyIndicator\n            rateAmount(currencyCode: $currencyCode)\n            rateAmountFmt(decimal: 0, strategy: ceiling)\n            ratePlanCode\n            ratePlan {\n              ratePlanName @toTitleCase\n              ratePlanDesc\n            }\n          }\n        }\n      }\n    }\n    ctyhocnList: hotelSummaryOptions(distanceUnit: $distanceUnit, sortBy: distance) {\n      hotelList: hotels {\n        ctyhocn\n      }\n    }\n  }\n  geocodePageEn: geocodePage(language: "en", path: $path) {\n    match {\n      name\n    }\n  }\n}',
                "operationName": "hotelSummaryOptions_geocodePage",
                "variables": {
                    "path": location_url,
                    "language": "en",
                    "queryLimit": 150,  # server-enforced maximum
                    "currencyCode": "USD",
                    "titleFormat": "md",
                    "input": {"guestLocationCountry": "US"},
                },
            }
        )
        headers = {
            "content-type": "application/json",
        }

        return requests.post(url, headers=headers, data=payload)
