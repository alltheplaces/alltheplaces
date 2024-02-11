from copy import copy
from urllib.parse import quote

from scrapy import Spider

from locations.dict_parser import DictParser


class CukierniaSowaPLSpider(Spider):
    name = "cukiernia_sowa_pl"
    item_attributes = {"brand": "Cukiernia Sowa", "brand_wikidata": "Q113232449"}
    start_urls = ["https://www.cukierniasowa.pl/home/shops?str=&reg=&type=0&geo=&alias=&typee=&count="]

    def parse(self, response, **kwargs):
        for shop in response.json():
            for key, value in copy(shop).items():
                if key.startswith("location_"):
                    shop[key.removeprefix("location_")] = value
            item = DictParser.parse(shop)
            item["website"] = f"https://www.cukierniasowa.pl/cukiernie/{quote(shop['url'])}"
            # TODO: shop["hours"] has PHP serialized opening hours. loads from phpserialize?
            yield item
