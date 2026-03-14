import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class BostonMarketUSSpider(Spider):
    name = "boston_market_us"
    item_attributes = {"brand": "Boston Market", "brand_wikidata": "Q603617"}
    allowed_domains = ["www.bostonmarket.com"]
    start_urls = ["https://www.bostonmarket.com/store-location.txt"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # HTML 404 page causes robots.txt parse warnings

    def parse(self, response: Response) -> Iterable[Request]:
        if matches := re.findall(r"static\/chunks\/\d+-[0-9a-f]+\.js", response.text):
            js_files = list(set(matches))
            for js_file in js_files:
                yield Request(url=f"https://www.bostonmarket.com/_next/{js_file}", callback=self.parse_js_file)

    def parse_js_file(self, response: Response) -> Iterable[Feature]:
        if '{name:"Boston Market Corporation",position:{lat:' not in response.text:
            # Not the JavaScript file we want that contains restaurant
            # location information.
            return

        js_blob = (
            '[{name:"Boston Market Corporation",'
            + response.text.split('=[{name:"Boston Market Corporation",', 1)[1].split("}]", 1)[0]
            + "}]"
        )
        features = parse_js_object(js_blob)
        for feature in features:
            if feature["status"] != "Open":
                continue
            item = DictParser.parse(feature)
            item["ref"] = str(feature["storeNumber"])
            item.pop("name", None)
            apply_category(Categories.FAST_FOOD, item)
            yield item
