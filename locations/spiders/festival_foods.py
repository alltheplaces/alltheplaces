from scrapy import Spider

from locations.dict_parser import DictParser


class FestivalFoodsSpider(Spider):
    name = "festival_foods"
    item_attributes = {
        "brand": "festival_foods",
        "brand_wikidata": "Q5445707",
        "country": "US",
    }
    start_urls = ["https://api.freshop.com/1/stores?app_key=festival_foods_envano"]

    def parse(self, response):
        for store in response.json()["items"]:
            # Other types are not stores
            if store["type_id"] != "1567647":
                continue

            # 6449 is "Festival Gift Cards", not a physical location
            if store["id"] == "6449":
                continue

            item = DictParser.parse(store)

            item["street_address"] = store["address_1"]

            item["website"] = "https://www.festfoods.com" + store["url"]

            if store.get("identifier"):
                item["ref"] = store["identifier"]

            yield item
