import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours


class PumaTWSpider(SitemapSpider):
    name = "puma_tw"
    item_attributes = {
        "brand": "Puma",
        "brand_wikidata": "Q157064",
    }

    # Note, /api/search is forbidden by robots.txt
    sitemap_urls = ["https://tw.puma.com/Sitemap/40187/Sitemap_Index.xml"]
    sitemap_rules = [
        (r"/Shop/StoreDetail/[^/]+/[^/]+$", "parse"),
    ]

    def parse(self, response):
        store = chompjs.parse_js_object(
            response.xpath('//script[contains(text(),"nineyi.ServerData")]/text()').extract_first()
        )
        item = DictParser.parse(store)
        item["opening_hours"] = OpeningHours()
        self.opening_hours_add(DAYS_WEEKDAY, store.get("NormalTime"), item)
        self.opening_hours_add(DAYS_WEEKEND, store.get("WeekendTime"), item)

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item

    def opening_hours_add(self, days, store_hours, item):
        for day in days:
            open = store_hours.split("~")[0]
            close = store_hours.split("~")[1]
            item["opening_hours"].add_range(day, open, close)
