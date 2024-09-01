import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, OpeningHours, sanitise_day


class HaraldNyborgDKSpider(Spider):
    name = "harald_nyborg_dk"
    start_urls = ["https://www.harald-nyborg.dk/butikker"]
    item_attributes = {"brand": "Harald Nyborg", "brand_wikidata": "Q12315668"}

    def parse(self, response, **kwargs):
        for store in json.loads(
            response.xpath('//*[contains(text(),"contentBlockGroups")]/text()').re_first(
                r"physicalShops\":\s*(.*),\s*\"blockTypeName"
            )
        ):
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full", "")
            item["branch"] = item.pop("name")
            day_time = store.get("openingHours")
            item["opening_hours"] = OpeningHours()
            for day, open_time, close_time in re.findall(r"<td>(\w+):</td><td>(\d+\.\d+)+\s*-\s*(\d+\.\d+)", day_time):
                day = sanitise_day(day, DAYS_DK)
                item["opening_hours"].add_range(day, open_time, close_time, time_format="%H.%M")
            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item
