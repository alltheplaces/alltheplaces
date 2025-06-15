from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours


class LevisTWSpider(SitemapSpider):
    name = "levis_tw"
    item_attributes = {"brand": "Levi's", "brand_wikidata": "Q127962"}
    sitemap_urls = ["https://www.levis.com.tw/robots.txt"]
    sitemap_rules = [(r"/Shop/StoreDetail/\d+/\d+", "parse")]
    sitemap_follow = ["ShopLocation"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = chompjs.parse_js_object(response.xpath('//script[contains(text(),"ServerData")]').get())
        if not location.get("Address"):
            return
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        for days, timing in [(DAYS_WEEKDAY, "NormalTime"), (DAYS_WEEKEND, "WeekendTime")]:
            item["opening_hours"].add_days_range(days, *location[timing].split("~"))
        yield item
