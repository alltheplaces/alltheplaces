import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HachibanRamenTHSpider(scrapy.Spider):
    name = "hachiban_ramen_th"
    item_attributes = {"brand": "Hachiban Ramen", "brand_wikidata": "Q11326388"}
    start_urls = ["https://www.hachiban.co.th/en/branch/"]

    def parse(self, response, **kwargs):
        data = response.xpath("//body//script").xpath("normalize-space()").re_first(r"Sheet1\"\s*:\s*(\[.*\])\s*};")
        for restaurant in chompjs.parse_js_object(data):
            item = DictParser.parse(restaurant)
            item["branch"] = restaurant.get("NAME_EN").strip()
            item["ref"] = restaurant.get("CODE")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(restaurant["OPEN_CLOSE"])
            apply_category(Categories.RESTAURANT, item)
            yield item
