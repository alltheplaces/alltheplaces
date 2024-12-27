from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class IonitySpider(Spider):
    name = "ionity"
    BRANDS = {
        "Ionity": ("Ionity", "Q42717773"),
        "Tesla Supercharger": ("Tesla Supercharger", "Q17089620"),
        "EnBW": ("EnBW", "Q644304"),
        "A2A": ("A2A", "Q279978"),
        "AGSM AIM": ("AGSM AIM", "Q124713351"),
        "Aral pulse": ("Aral pulse", "Q130210067"),
        "Atlante": ("Atlante", "Q126913632"),
        "Be Charge": ("Be Charge", "Q113289535"),
        "Compleo": ("Compleo", "Q117765911"),
        "Energie Calw GmbH": ("Energie Calw", "Q130427211"),
        "Hamburger Energiewerke Mobil": ("Hamburger Energiewerke", "Q113465071"),
        "illwerke vkw AG": ("illwerke vkw", "Q97012080"),
        # TODO: add more brands with their wikidata
    }
    SOCKET_MAP = {
        "CHADEMO": "chademo",
        "IEC_62196_T2": "type2",
        "IEC_62196_T2_COMBO": "type2_combo",
        "IEC_62196_T3A": "type3a",
        "TESLA_S": "tesla_supercharger",
    }

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def make_request(self, page: int, size: int = 100) -> JsonRequest:
        return JsonRequest(
            url="https://api.chargetrip.io/graphql",
            data={
                "operationName": "StationList",
                "variables": {
                    "page": page,
                    "size": size,
                },
                "query": """
                    query StationList($page: Int, $size: Int) {
                        stationList(page: $page, size: $size) {
                            id
                            country_code
                            party_id
                            publish
                            name
                            street_address: address
                            location {
                             type 
                             coordinates
                            }
                            city
                            postal_code
                            state
                            country
                            parking_type
                            facilities
                            time_zone
                            opening_times {
                                twentyfourseven
                                regular_hours {
                                    weekday
                                    period_begin
                                    period_end
                                }
                            }
                            chargers {
                                standard
                                power
                                price
                                speed
                                total
                            }
                            charging_when_closed
                            last_updated
                            external_id
                            elevation
                            amenities
                            images{
                                url
                            }
                            location_category
                            properties
                            realtime
                            private
                            power
                            speed
                            status
                            phone:support_phone_number
                            reliability_score
                            adhoc_authorisation_payment_method
                            access_type
                            operator {
                                id
                                name
                                website
                            }
                            owner {
                                id
                                name
                                website
                            }
                        }
                    }
                """,
            },
            headers={
                "Origin": "https://playground.chargetrip.com",
                "Referer": "https://playground.chargetrip.com/",
                "x-app-id": "623996f3c35130073829b252",
                "x-client-id": "5ed1175bad06853b3aa1e492",
            },
            meta=dict(page=page, size=size),
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if station_list := response.json().get("data", {}).get("stationList"):
            for station in station_list:
                item = DictParser.parse(station)
                item["geometry"] = station["location"]
                item["operator"] = station["operator"]["name"] if station["operator"] else None
                brand = station["owner"]["name"] if station["owner"] else None
                if brand_info := self.BRANDS.get(brand):
                    item["brand"], item["brand_wikidata"] = brand_info
                else:
                    item["brand"] = brand
                item["website"] = station["owner"]["website"] if station["owner"] else None
                item["extras"]["operator:website"] = station["operator"]["website"] if station["operator"] else None
                if station["chargers"]:
                    for socket in station["chargers"]:
                        if match := self.SOCKET_MAP.get(socket["standard"]):
                            item["extras"][f"socket:{match}"] = str(socket["total"])
                            item["extras"][f"socket:{match}:output"] = f'{socket["power"]} kW'

                item["opening_hours"] = OpeningHours()
                if station["opening_times"]["twentyfourseven"]:
                    item["opening_hours"] = "24/7"
                else:
                    for rule in station["opening_times"]["regular_hours"]:
                        if rule.get("period_begin") and rule.get("period_end"):
                            item["opening_hours"].add_range(
                                DAYS[rule["weekday"] - 1], rule["period_begin"], rule["period_end"]
                            )

                apply_category(Categories.CHARGING_STATION, item)
                yield item

            if len(station_list) == response.meta["size"]:
                yield self.make_request(response.meta["page"] + 1)
