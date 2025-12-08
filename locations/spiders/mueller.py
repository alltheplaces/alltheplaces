from typing import Any, AsyncIterator

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MuellerSpider(Spider):
    name = "mueller"
    item_attributes = {"brand": "Müller", "brand_wikidata": "Q1958759"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    api = "https://backend.prod.ecom.mueller.de/"
    headers = {}

    async def start(self) -> AsyncIterator[Request]:
        for country, url in [
            ("AT", "https://www.mueller.at/storefinder/"),
            ("CH", "https://www.mueller.ch/storefinder/"),
            ("DE", "https://www.mueller.de/storefinder/"),
            ("ES", "https://www.mueller.es/mis-tiendas/"),
            ("HR", "https://www.mueller.hr/moja-poslovnica/"),
            ("HU", "https://www.mueller.co.hu/mueller-uezletek/"),
            ("SI", "https://www.mueller.si/poslovalnice/"),
        ]:
            yield Request(url=url, cb_kwargs=dict(country=country))

    def parse(self, response: Response, country: str) -> Any:
        data = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        auth_details = data["props"]["pageProps"]["graphqlSettings"]["publicHost"]["header"]
        self.headers = {auth_details["key"]: auth_details["value"]}
        yield JsonRequest(
            url=self.api,
            data={
                "query": """
                    query GetStores($country: String!) {
                        getStores(country: $country) {
                            code
                            }
                    }
                """,
                "operationName": "GetStores",
                "variables": {
                    "country": country,
                },
            },
            headers=self.headers,
            callback=self.parse_store_ids,
            cb_kwargs=dict(country=country),
        )

    def parse_store_ids(self, response: Response, country: str) -> Any:
        stores = response.json()["data"]["getStores"]
        # Don't pull the data for whole list of stores in one go, to avoid non-responsive behaviour of API.
        batch_size = 25
        for i in range(0, len(stores), batch_size):
            yield JsonRequest(
                url=self.api,
                data={
                    "query": """
                            query GetStoresByIds($storeIds: [String!]!, $country: String!) {
                                getStoresByIds(storeIds: $storeIds, country: $country) {
                                    id: code
                                    address {
                                        street_address: street
                                        zip
                                        town
                                    }
                                    assortments
                                    company{
                                        name
                                    }
                                    email
                                    geoLocation{
                                        lat
                                        lng
                                    }
                                    name
                                    openingHours{
                                        day
                                        openingTime
                                        closingTime
                                        startPauseTime
                                        endPauseTime
                                    }
                                    phone
                                    pickupTime
                                }
                            }
                            """,
                    "operationName": "GetStoresByIds",
                    "variables": {
                        "storeIds": [store["code"] for store in stores[i : i + batch_size]],
                        "country": country,
                    },
                },
                headers=self.headers,
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["getStoresByIds"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["phone"] = store["phone"].replace("/", "") if store["phone"] else None
            item["opening_hours"] = OpeningHours()
            for rule in store["openingHours"]:
                if rule["openingTime"] and rule["closingTime"]:
                    item["opening_hours"].add_range(rule["day"], rule["openingTime"], rule["closingTime"])
            yield item
