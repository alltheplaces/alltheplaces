from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ScotmidSpider(Spider):
    name = "scotmid"
    item_attributes = {
        "brand": "Scotmid",
        "brand_wikidata": "Q7435719",
        "country": "GB",
    }
    start_urls = ["https://scotmid.coop/store/"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)

            type = store.get("style")
            item["extras"] = {}
            item["extras"]["type"] = type

            if type == "post-offices":
                # Skip post offices
                continue
            elif type == "scotmid":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif type == "semichem":
                item["brand"] = "Semichem"
                item["brand_wikidata"] = "Q17032096"
            elif type == "lakes-and-dales":
                item["brand"] = "Lakes & Dales Co-operative"
                item["brand_wikidata"] = "Q110620660"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif type == "funeral-branches":
                item["brand"] = "Scotmid Funerals"
                item["brand_wikidata"] = "Q125940846"
                apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

            item["name"] = store.get("title")

            item["street_address"] = store.get("address_line_1")
            item["city"] = store.get("address_line_2")
            item["state"] = store.get("address_line_3")

            item["phone"] = store.get("telephone_number")

            if "slug" in store:
                item["website"] = "https://scotmid.coop/store/" + store["slug"] + "/"

            oh = OpeningHours()
            for day in [
                "mon",
                "tue",
                "wed",
                "thu",
                "fri",
                "sat",
                "sun",
            ]:
                open_time = store.get("ot_" + day + "_open")
                close_time = store.get("ot_" + day + "_close")

                if open_time is None or close_time is None:
                    continue

                if len(open_time) == 4:
                    open_time = open_time[0:2] + ":" + open_time[2:4]
                if len(close_time) == 4:
                    close_time = close_time[0:2] + ":" + close_time[2:4]

                try:
                    oh.add_range(day[:2].title(), open_time, close_time)
                except ValueError:
                    pass

            item["opening_hours"] = oh.as_opening_hours()

            yield item
