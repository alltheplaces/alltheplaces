import pycountry
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class LegoSpider(JSONBlobSpider):
    name = "lego"
    item_attributes = {"brand": "Lego", "brand_wikidata": "Q1063455", "extras": Categories.SHOP_TOYS.value}
    # locations_key = ["data", "storeSearch", "stores"]
    download_timeout = 30

    def start_requests(self):
        for country in pycountry.countries:
            yield JsonRequest(
                url="https://www.lego.com/api/graphql/StoreSearch",
                data={
                    "operationName": "StoreSearch",
                    "variables": {"location": country.name},
                    "query": "query StoreSearch($location: String) {\n  storeSearch(location: $location) {\n    geometry {\n      viewport {\n        northeast {\n          lat\n          lng\n          __typename\n        }\n        southwest {\n          lat\n          lng\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    stores {\n      storeId\n      name\n      phone\n      streetAddress\n      city\n      state\n      postalCode\n      storeUrl\n      openingTimes {\n        day\n        timeRange\n        __typename\n      }\n      urlKey\n      coordinates {\n        lat\n        lng\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}",
                },
            )

    def extract_json(self, response):
        json_data = response.json()["data"]["storeSearch"]
        if json_data is not None:
            return json_data["stores"]
        else:
            return []

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("LEGO® Store ", "")
        if item["website"] == "store.default.url":
            item["website"] = "https://www.lego.com/stores/store/" + location["urlKey"]
        item["ref"] = item["website"]  # stores have "storeId" field, but it is not unique

        item["opening_hours"] = OpeningHours()
        for day in location["openingTimes"]:
            item["opening_hours"].add_ranges_from_string(day["day"] + " " + day["timeRange"])

        yield item
