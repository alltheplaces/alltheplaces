from chompjs import parse_js_object
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class AquilaAUSpider(Spider):
    name = "aquila_au"
    item_attributes = {"brand": "Aquila", "brand_wikidata": "Q17985574"}
    allowed_domains = ["www.aquila.com.au"]
    start_urls = ["https://www.aquila.com.au/store-locator"]

    def parse(self, response: Response) -> Iterable[Request]:
        js_blob = response.xpath('//script[contains(text(), "storesInfo_scriptManager = ")]/text()').get()
        js_blob = re.sub(r"\s+", " ", js_blob.split("storesInfo_scriptManager = ", 1)[1].split("];", 1)[0] + "]")
        features = parse_js_object(js_blob)
        for feature in features:
            item = DictParser.parse(feature)
            if feature["name"].startswith("Aquila Myer"):
                item["located_in"] = "Myer"
                item["located_in_wikidata"] = "Q1110323"
                item["branch"] = item.pop("name", None).removeprefix("Aquila Myer ").removesuffix(" Store")
            else:
                item["branch"] = item.pop("name", None).removeprefix("Aquila ").removesuffix(" Store")
            item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"].replace("<br>", " ").replace("<b>", "").replace("</b>", "")).strip()
            item["website"] = "https://www.aquila.com.au/store-locator/" + feature["id"]
            item["ref"] = item["website"]
            apply_category(Categories.SHOP_SHOES, item)
            yield Request(url=item["ref"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        hours_text = re.sub(r"\s+", " ", " ".join(response.xpath('//div[@class="js-store-description"]//td/text()').getall()))
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
