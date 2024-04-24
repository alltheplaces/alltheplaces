from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DunelmGBSpider(Spider):
    name = "dunelm_gb"
    item_attributes = {"name": "Dunelm", "brand": "Dunelm", "brand_wikidata": "Q5315020"}

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
            item["branch"] = item.pop("name")
            item["ref"] = store["sapStoreId"]
            item["website"] = "https://www.dunelm.com/stores/" + store["uri"]

            oh = OpeningHours()
            for rule in store["openingHours"]:
                oh.add_range(rule["day"], rule["open"], rule["close"])

            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
            yield item
