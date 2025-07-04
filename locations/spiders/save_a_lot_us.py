from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SaveALotUSSpider(SitemapSpider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972"}
    sitemap_urls = ["https://savealot.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"window.__remixContext")]/text()').get()
        )["state"]["loaderData"]["routes/stores.$storeId._index"]["storeDetailsV2"]
        raw_data.update(raw_data.pop("location"))
        item = DictParser.parse(raw_data)
        item["branch"] = item.pop("name")
        item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        for day_time in raw_data["hours"]["weekly"]:
            day = day_time["day"]
            if day_time["daily"]["type"] == "CLOSED":
                item["opening_hours"].set_closed(day_time["day"])
            elif day_time["daily"]["type"] == "OPEN_24_HOURS":
                item["opening_hours"].add_range(day_time["day"], "00:00", "24:00")
            else:
                open_time = day_time["daily"]["open"]["open"]
                close_time = day_time["daily"]["open"]["close"]
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                )

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
