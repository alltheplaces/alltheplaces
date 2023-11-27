from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DunelmGB(Spider):
    name = "dunelm_gb"
    item_attributes = {
        "brand": "Dunelm",
        "brand_wikidata": "Q5315020",
        "extras": {"shop": "houseware"},
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://fy8plebn34-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id=FY8PLEBN34&x-algolia-api-key=ae9bc9ca475f6c3d7579016da0305a33",
            data={
                "requests": [
                    {
                        "indexName": "stores_prod",
                        "params": "hitsPerPage=300",
                    }
                ]
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["results"][0]["hits"]:
            store["location"] = store["_geoloc"]

            item = DictParser.parse(store)

            item["ref"] = store["sapStoreId"]
            item["website"] = "https://www.dunelm.com/stores/" + store["uri"]

            oh = OpeningHours()
            for rule in store["openingHours"]:
                oh.add_range(rule["day"], rule["open"], rule["close"])

            item["opening_hours"] = oh.as_opening_hours()

            item["extras"] = {"storeType": store.get("storeType")}

            yield item
