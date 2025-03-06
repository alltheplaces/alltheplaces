import scrapy
from geonamescache import GeonamesCache
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.country_utils import get_locale
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class MitsubishiSpider(scrapy.Spider):
    """
    API for the spider is found on https://www.mitsubishi-motors.co.th/en/dealer-locator.
    At the time of writing it covers dealers for below countries:
    AT, BH, CA, EG, ES, FI, GR, IT, KW, MX,
    NL, NO, OM, PR, PT, QA, RO, TH, US
    """

    name = "mitsubishi"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    handle_httpstatus_list = [403]

    def start_requests(self):
        countries = GeonamesCache().get_countries().keys()
        for country in countries:
            locale = get_locale(country)
            language = locale.split("-")[0] if locale else "en"
            yield JsonRequest(
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
                    "variables": {"market": country.lower(), "language": language},
                },
                meta={"country": country, "language": language},
            )

    def get_details(self, country, language, dealer_id, item):
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
                item["website"] = poi.get("url")
                yield from self.get_details(country, language, poi.get("id"), item)

    def parse_details(self, response):
        item = response.meta["item"]
        details = response.json()["data"].get("getDealerDetail")
        department_codes = [d.get("code") for d in details.get("dealerDepartments", [])]
        # TODO: opening hours are available in dealerDepartments

        if "sales" in department_codes:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no("service:vehicle:car_repair", item, "services" in department_codes, True)
        elif "services" in department_codes:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            self.logger.error(f"Unknown department codes: {department_codes}, {item['ref']}")

        for code in department_codes:
            self.crawler.stats.inc_value(f"atp/{self.name}/department_codes/{code}")

        yield item
