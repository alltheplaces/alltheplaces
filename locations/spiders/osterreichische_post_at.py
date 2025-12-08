from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_AT, OpeningHours, sanitise_day

POST_AT = {"operator": "Österreichische Post AG", "operator_wikidata": "Q1763505"}


class OsterreichischePostATSpider(Spider):
    name = "osterreichische_post_at"
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.post.at/branchservice/core/graphql",
            data={
                "query": """query {
                                branches {
                                    branchkey
                                    isactive
                                    longname
                                    name
                                    orgpostalcode
                                    type
                                    address {
                                        country
                                        pac
                                        postalcode
                                        streetname
                                        streetnumber
                                        city
                                        coordinates {
                                            latitudewgs84
                                            longitudewgs84
                                        }
                                    }
                                    contact {
                                        emailaddress
                                        phonenumber
                                    }
                                    standardstorehours {
                                        closinghour
                                        openinghour
                                        dayofweek
                                        middayclosures {
                                            closinghour
                                            openinghour
                                        }
                                    }
                                }
                            }""",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["branches"]:
            if location["isactive"] is False:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["branchkey"]
            item["lat"] = location["address"]["coordinates"]["latitudewgs84"]
            item["lon"] = location["address"]["coordinates"]["longitudewgs84"]
            item["website"] = "https://www.post.at/en/sf/locationfinder?branch={}".format(location["branchkey"])
            item["opening_hours"] = self.parse_opening_hours(location["standardstorehours"])

            if item["name"] != location["longname"]:
                item["extras"]["full_name"] = location["longname"]

            if location["type"] == "BRIEFKASTEN":
                item["name"] = None
                item.update(POST_AT)
                apply_category(Categories.POST_BOX, item)
            elif location["type"] == "POSTPARTNER":
                if ", " in location["longname"]:
                    item["name"] = location["longname"].split(", ", 1)[1]
                else:
                    item["name"] = None
                item["extras"]["post_office:brand"] = "Österreichische Post"
                apply_category(Categories.GENERIC_POI, item)
                apply_yes_no("post_office=post_partner", item, True)
            elif location["type"] == "FILIALE":
                item.update(POST_AT)
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] == "ABHOLSTATION":
                item["name"] = None
                item.update(POST_AT)
                apply_category(Categories.PARCEL_LOCKER, item)
            elif location["type"] in ("PAKET_PUNKT", "HERMES"):
                continue
            else:
                self.logger.warning("Unexpected type: {}".format(location["type"]))
                continue

            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules or []:
            day = sanitise_day(rule["dayofweek"], DAYS_AT)
            if rule["middayclosures"]:
                oh.add_range(day, rule["openinghour"], rule["middayclosures"]["closinghour"], time_format="%H:%M:%S")
                oh.add_range(day, rule["middayclosures"]["openinghour"], rule["closinghour"], time_format="%H:%M:%S")
            else:
                oh.add_range(day, rule["openinghour"], rule["closinghour"], time_format="%H:%M:%S")
        return oh
