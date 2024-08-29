import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SportMasterDKSpider(Spider):
    name = "sport_master_dk"
    item_attributes = {"brand": "Sportmaster", "brand_wikidata": "Q61062124"}
    start_urls = [
        "https://sportmaster.dk/butik",
    ]

    def parse(self, response, **kwargs):
        for store in json.loads(response.xpath("//*/@data-json").get()).get("store").get("list"):
            item = DictParser.parse(store)
            item["website"] = "https://sportmaster.dk" + item["website"]
            item["opening_hours"] = OpeningHours()
            for day_time in store.get("openingHours"):
                if day_time.get("value") not in ["Not working", "null", None, "null - null"]:
                    open_time, close_time = day_time.get("value").split(" - ")
                day = DAYS[int(day_time.get("weekDay")) - 1]
                item["opening_hours"].add_range(day, open_time, close_time)
            apply_category(Categories.SHOP_SPORTS, item)

            yield item
