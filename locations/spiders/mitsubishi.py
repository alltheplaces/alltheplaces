from copy import deepcopy
from typing import AsyncIterator, Iterable

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.country_utils import get_locale
from locations.dict_parser import DictParser
from locations.hours import (
    DAYS_DE,
    DAYS_EN,
    DAYS_ES,
    DAYS_FI,
    DAYS_IT,
    DAYS_NL,
    DAYS_NO,
    DAYS_PT,
    DAYS_RO,
    OpeningHours,
    sanitise_day,
)
from locations.pipelines.address_clean_up import clean_address


class MitsubishiSpider(Spider):
    """
    API for the spider is found on https://www.mitsubishi-motors.co.th/en/dealer-locator.
    At the time of writing it covers dealers for below countries:
    AT, BH, CA, EG, ES, FI, IT, KW, NL, NO, OM, PH, PR, PT, QA, RO, TH, US
    """

    name = "mitsubishi"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    handle_httpstatus_list = [403]

    async def start(self) -> AsyncIterator[JsonRequest]:
        countries = list(GeonamesCache().get_countries().keys())
        countries.remove("BE")  # mitsubishi_be_lu
        for country in countries:
            locale = get_locale(country)
            language = locale.split("-")[0] if locale else "en"
            country = country.lower()
            yield self.get_locations(country, language)

    def get_locations(self, country, language) -> JsonRequest:
        return JsonRequest(
            url="https://www-graphql.prod.mipulse.co/prod/graphql",
            data={
                "query": """
                query SearchDealer($market: String!, $language: String!) {
                    searchDealer(criteria: { market: $market, language: $language }) {
                        id
                        dealershipMarketId
                        name
                        isActive
                        url
                        email
                        dealerFilterTags
                        phone {
                            phoneNumber
                        }
                        address {
                            country
                            city
                            district
                            municipality
                            postcode: postalArea
                            longitude
                            latitude
                            addressLine1
                            addressLine2
                            addressLine3
                        }
                    }
                }""",
                "variables": {"market": country, "language": language},
            },
            meta={"country": country, "language": language},
            callback=self.parse,
        )

    def get_details(self, country, language, dealer_id, item) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://www-graphql.prod.mipulse.co/prod/graphql",
            data={
                "query": """
                query getDealerDetail($market: String!, $language: String!, $dealerId: Int!) {
                    getDealerDetail(market: $market, language: $language, dealerId: $dealerId) {
                        email
                        phone {
                            phoneType
                            countryCode
                            areaCode
                            phoneNumber
                            extensionNumber
                        }
                        dealerFilterTags
                        dealerDepartments {
                            name
                            code
                            email
                            phone {
                                phoneType
                                countryCode
                                areaCode
                                phoneNumber
                                extensionNumber
                            }
                            workingHours {
                                dayOfTheWeek
                                openTime
                                closeTime
                                status
                            }
                        }
                        scheduleServiceUrl
                        searchInventoryUrl
                    }
                }
                """,
                "variables": {"market": country.lower(), "language": language, "dealerId": dealer_id},
            },
            meta={"item": item},
            callback=self.parse_details,
        )

    def parse(self, response, **kwargs):
        country = response.meta["country"]
        language = response.meta["language"]

        if response.status in self.handle_httpstatus_list:
            self.logger.info(f"Failed request for {country}/{language} with {response.status} code")
            self.crawler.stats.inc_value(f"atp/{self.name}/request/failed/{country}/{language}/{response.status}")
        elif "errors" in response.json():
            self.logger.info(f"No dealers found for {country}/{language}")
            self.crawler.stats.inc_value(f"atp/{self.name}/dealers/not_found/{country}/{language}")

            # Fallback to English if no dealers found for country/language combination
            if language != "en":
                yield self.get_locations(country, "en")

        else:
            pois = response.json()["data"].get("searchDealer", [])
            self.logger.info(f"Found {len(pois)} dealers for {country}/{language}")

            for poi in pois:
                if poi.get("isActive", True) is not True:
                    continue
                poi.update(poi.pop("address"))
                item = DictParser.parse(poi)
                item.pop("street_address", None)
                # Addresses are inconsistent across countries, so we do addr_full
                # For some countries, mappings are provided.
                if item["country"] == "CA":
                    item["street_address"] = poi.get("addressLine1")
                    item["state"] = poi.get("district")
                elif item["country"] in ["US", "IT"]:
                    item["street_address"] = poi.get("addressLine1")
                    item["city"] = poi.get("addressLine2")
                    item["state"] = poi.get("addressLine3")
                elif item["country"] == "AT":
                    item["street_address"] = poi.get("addressLine1")
                    item["city"] = poi.get("addressLine2")
                elif item["country"] == "NO":
                    item["street_address"] = poi.get("addressLine1")
                    item["city"] = poi.get("district")
                elif item["country"] == "NL":
                    item["street_address"] = poi.get("addressLine1")
                    item["city"] = poi.get("addressLine3")
                elif item["country"] == "FI":
                    item["street_address"] = poi.get("addressLine1")
                else:
                    item["addr_full"] = clean_address(
                        [
                            poi.get("addressLine1", ""),
                            poi.get("addressLine2", ""),
                            poi.get("addressLine3", ""),
                            poi.get("city", ""),
                            poi.get("postcode", ""),
                        ]
                    )
                item["phone"] = poi.get("phone").get("phoneNumber")
                item["website"] = (poi.get("url") or "").replace("https://https://", "https://")
                yield from self.get_details(country, language, poi.get("id"), item)

    def build_sales_item(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse_details(self, response):
        item = response.meta["item"]
        details = response.json()["data"].get("getDealerDetail")
        department_codes = [d.get("code") for d in details.get("dealerDepartments", [])]
        sales_hours = next(
            (d.get("workingHours") for d in details.get("dealerDepartments", []) if d.get("code") == "sales"), []
        )
        service_hours = next(
            (d.get("workingHours") for d in details.get("dealerDepartments", []) if d.get("code") == "services"), []
        )
        sales_available = "sales" in department_codes
        service_available = "services" in department_codes

        if sales_available:
            sales_item = self.build_sales_item(item)
            sales_item["opening_hours"] = self.parse_hours(sales_hours, item["country"])
            apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
            yield sales_item

        if service_available:
            service_item = self.build_service_item(item)
            service_item["opening_hours"] = self.parse_hours(service_hours, item["country"])
            yield service_item

        if not sales_available and not service_available:
            self.logger.error(f"Unknown department codes: {department_codes}, {item['ref']}")

        for code in department_codes:
            self.crawler.stats.inc_value(f"atp/{self.name}/department_codes/{code}")

    def parse_hours(self, hours: list[dict], country) -> OpeningHours:
        OPEN_STATUS = ["Apri", "Open", "Öffnen", "เปิด", "Åpen", "Avaa", "Abierto", "Deschide", "Abrir"]
        CLOSE_STATUS = ["Chiudi", "Closed", "Schliessen"]
        DAYS_MAPPING = {
            "IT": DAYS_IT,
            "NO": DAYS_NO,
            "AT": DAYS_DE,
            "NL": DAYS_NL,
            "FI": DAYS_FI,
            "PR": DAYS_ES,
            "RO": DAYS_RO,
            "ES": DAYS_ES,
            "PT": DAYS_PT,
        }
        try:
            oh = OpeningHours()
            days = DAYS_MAPPING.get(country, DAYS_EN)
            for schedule in hours:
                day = sanitise_day(schedule["dayOfTheWeek"], days)
                if schedule["status"] in OPEN_STATUS:
                    oh.add_ranges_from_string(ranges_string=f"{day}: {schedule['openTime']}")
                elif schedule["status"] in CLOSE_STATUS:
                    oh.set_closed(day)
            return oh
        except Exception as e:
            self.logger.warning("Error parsing {} {}".format(hours, e))
