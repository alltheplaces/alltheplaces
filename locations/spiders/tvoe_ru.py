import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TvoeRUSpider(Spider):
    name = "tvoe_ru"
    item_attributes = {"brand": "ТВОЕ", "brand_wikidata": "Q110034939"}
    start_urls = ["https://tvoe.ru/contacts/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop in json.loads(response.xpath('//component[@is="shops"]').attrib.get(":shops")):
            item = DictParser.parse(shop)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            oh = OpeningHours()
            open_time, close_time = shop.get("workhours").replace(" ", "").split("-")
            oh.add_days_range(DAYS, open_time, close_time)
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
