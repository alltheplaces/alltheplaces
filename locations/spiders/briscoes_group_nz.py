import json
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BriscoesGroupNZSpider(Spider):
    name = "briscoes_group_nz"
    BRANDS = {
        "briscoes": ("Briscoes", "Q110190653"),
        "rebelsport": ("Rebel Sport", "Q110190372"),
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for brand in self.BRANDS:
            graphql_query = "query FindAllStores{findStore{store_id scope_id store_enable store_locator_name is_display_store_finder remove_from_refund latitude longitude working_time cut_off_time oms_store_id store_number fulfilment_number dispatch_point_name enable_next_day_delivery same_day_delivery organization line1 line2 city region postcode country_code state email phone __typename}}&operationName=FindAllStores&variables={}"
            url = "https://www.{}.co.nz/graphql?query={}".format(brand, graphql_query)
            headers = {"store": brand}
            yield JsonRequest(url=url, headers=headers, callback=self.parse)

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["findStore"]:
            # weed out popup stores
            if store["is_display_store_finder"]:
                item = DictParser.parse(store)
                brand = response.url.split(".")[1]
                username = item["email"].split("@")[0]
                if username in ["info", "online"]:
                    item["email"] = ""
                item["name"] = store["store_locator_name"]
                item["branch"] = item.pop("name").removeprefix("Rebel Sport ").removeprefix("Briscoes ")
                item["opening_hours"] = OpeningHours()
                for rules in json.loads(store["working_time"]):
                    item["opening_hours"].add_range(rules["day_of_week"], rules["open_time"], rules["close_time"])
                if brand_details := self.BRANDS.get(brand):
                    item["brand"], item["brand_wikidata"] = brand_details
                yield item
