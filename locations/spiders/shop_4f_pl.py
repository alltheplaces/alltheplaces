from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class Shop4fPL(Spider):
    name = "shop_4f_pl"
    item_attributes = {"brand": "4F", "brand_wikidata": "Q16525801"}
    start_urls = [
        "https://4f.com.pl/graphql?query=query+GetShops%28%24store_id%3AInt%29%7BstationaryShops%28store_id%3A%24store_id%29%7Bid+name+country_id+city+postcode+address+telephone+email+description+latitude+longitude+type+active+personal_collection_enabled+wms_id+short_code+__typename%7D%7D&operationName=GetShops&variables=%7B%22store_id%22%3A1%7D"
    ]

    def parse(self, response: Response, **kwargs):
        for shop in response.json()["data"]["stationaryShops"]:
            if shop["active"] != "1":
                continue

            item = DictParser.parse(shop)
            item["street_address"] = shop["address"]
            del item["addr_full"]

            yield item
