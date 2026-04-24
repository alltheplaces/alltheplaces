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

                    try:
                        hotels_summary = response.json()["data"]["geocodePage"].get("hotelSummaryOptions") or {}
                        for poi in hotels_summary.get("hotels", []):
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
                    except:
                        self.logger.error(f'Error parsing locations for path: {region["locationPageUri"]}')

    def get_hotels(self, location_url: str):
        # TODO: we should use JsonRequest here, but it doesn't work with this endpoint for some reason!
        url = "https://www.hilton.com/graphql/customer?appName=dx_shop_search_app&operationName=hotelSummaryOptions_geocodePage&originalOpName=hotelSummaryOptions_geocodePage&bl=en"

        payload = json.dumps(
            {
                "query": """
                        query hotelSummaryOptions_geocodePage(
                          $language: String!,
                          $path: String!,
                          $queryLimit: Int!,
                          $currencyCode: String!,
                          $distanceUnit: HotelDistanceUnit,
                          $titleFormat: MarkdownFormatType!,
                          $input: HotelSummaryOptionsInput
                        ) {
                          geocodePage(language: $language, path: $path) {
                            location {
                              pageInterlinks {
                                title
                                links {
                                  name
                                  uri
                                }
                              }
                              title(format: $titleFormat)
                              accessibilityTitle
                              meta {
                                pageTitle
                                description
                              }
                              name
                              brandCode
                              category
                              uri
                              globalBounds
                              breadcrumbs {
                                uri
                                name
                              }
                              about {
                                contentBlocks {
                                  title(format: text)
                                  descriptions
                                  orderedList
                                  unorderedList
                                }
                                contentBlocks_noTx: contentBlocks {
                                  title(format: text)
                                  descriptions
                                  orderedList
                                  unorderedList
                                }
                                isContentLocalized
                              }
                              paths {
                                base
                              }
                              hotelSummaryExtractUrl
                            }
                            match {
                              address {
                                city
                                country
                                countryName
                                state
                                stateName
                              }
                              geometry {
                                location {
                                  latitude
                                  longitude
                                }
                                bounds {
                                  northeast {
                                    latitude
                                    longitude
                                  }
                                  southwest {
                                    latitude
                                    longitude
                                  }
                                }
                              }
                              id
                              name
                              type
                            }
                            hotelSummaryOptions(
                              distanceUnit: $distanceUnit
                              sortBy: distance
                              input: $input
                            ) {
                              _hotels {
                                totalSize
                              }
                              bounds {
                                northeast {
                                  latitude
                                  longitude
                                }
                                southwest {
                                  latitude
                                  longitude
                                }
                              }
                              amenities {
                                id
                                name
                                hint
                              }
                              amenityCategories {
                                name
                                id
                                amenityIds
                              }
                              brands {
                                code
                                name
                              }
                              hotels(first: $queryLimit) {
                                amenityIds
                                brandCode
                                ctyhocn
                                distance
                                distanceFmt
                                facilityOverview {
                                  allowAdultsOnly
                                  homeUrlTemplate
                                }
                                name
                                contactInfo {
                                  phoneNumber
                                }
                                display {
                                  open
                                  openDate
                                  preOpenMsg
                                  resEnabled
                                  resEnabledDate
                                  treatments
                                }
                                disclaimers {
                                  desc
                                  type
                                }
                                address {
                                  addressFmt
                                  addressLine1
                                  city
                                  country
                                  countryName
                                  postalCode
                                  state
                                  stateName
                                }
                                localization {
                                  currencyCode
                                  coordinate {
                                    latitude
                                    longitude
                                  }
                                }
                                images {
                                  master(ratios: [threeByTwo]) {
                                    altText
                                    ratios {
                                      size
                                      url
                                    }
                                  }
                                  carousel(ratios: [threeByTwo]) {
                                    altText
                                    ratios {
                                      url
                                      size
                                    }
                                  }
                                }
                                leadRate {
                                  lowest {
                                    cmaTotalPriceIndicator
                                    feeTransparencyIndicator
                                    rateAmount(currencyCode: $currencyCode)
                                    rateAmountFmt(decimal: 0, strategy: ceiling)
                                    ratePlanCode
                                    ratePlan {
                                      ratePlanName @toTitleCase
                                      ratePlanDesc
                                    }
                                  }
                                }
                              }
                            }
                            ctyhocnList: hotelSummaryOptions(distanceUnit: $distanceUnit, sortBy: distance) {
                              hotelList: hotels {
                                ctyhocn
                              }
                            }
                          }
                          geocodePageEn: geocodePage(language: "en", path: $path) {
                            match {
                              name
                            }
                          }
                        }
                """,
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
