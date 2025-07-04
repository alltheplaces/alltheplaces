from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SaveALotUSSpider(SitemapSpider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972", "extras": Categories.SHOP_SUPERMARKET.value}
    sitemap_urls = ["https://savealot.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"window.__remixContext")]/text()').get()
        )["state"]["loaderData"]["routes/stores.$storeId._index"]["storeDetailsV2"]
        raw_data.update(raw_data.pop("location"))
        print(raw_data)
        item = DictParser.parse(raw_data)
        item["branch"] = item.pop("name")
        item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        for day_time in raw_data["hours"]["weekly"]:
            day = day_time["day"]
            if day_time["daily"]["type"] == "CLOSED":
                continue
            if day_time["daily"]["type"] == "OPEN_24_HOURS":
                item["opening_hours"] = "24/7"
            else:
                open_time = day_time["daily"]["open"]["open"]
                close_time = day_time["daily"]["open"]["close"]
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                )
        yield item
