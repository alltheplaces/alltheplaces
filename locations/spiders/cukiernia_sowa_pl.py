from copy import copy
from urllib.parse import quote

from phpserialize import unserialize
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class CukierniaSowaPLSpider(Spider):
    name = "cukiernia_sowa_pl"
    item_attributes = {"brand": "Cukiernia Sowa", "brand_wikidata": "Q113232449"}
    start_urls = ["https://www.cukierniasowa.pl/home/shops?str=&reg=&type=0&geo=&alias=&typee=&count="]

    def parse(self, response, **kwargs):
        for shop in response.json():
            if shop["location_open"] == "0":
                continue
            for key, value in copy(shop).items():
                if key.startswith("location_"):
                    shop[key.removeprefix("location_")] = value
            item = DictParser.parse(shop)
            item["website"] = f"https://www.cukierniasowa.pl/cukiernie/{quote(shop['url'])}"
            item["street_address"] = item.pop("street")
            item["opening_hours"] = oh = OpeningHours()
            hours = unserialize(shop["hours"].encode(), decode_strings=True)
            for index, day in enumerate(DAYS, 1):
                rule = hours[index]
                if rule["disabled"] == "1":
                    oh.set_closed(day)
                else:
                    oh.add_range(
                        day,
                        "{hour}:{minute}".format(**rule["open"]),
                        "{hour}:{minute}".format(**rule["close"]),
                    )
            item.pop("name", None)
            apply_category(Categories.SHOP_PASTRY, item)
            yield item
