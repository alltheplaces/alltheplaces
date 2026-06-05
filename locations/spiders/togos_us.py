from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TogosUSSpider(SitemapSpider):
    name = "togos_us"
    item_attributes = {"brand": "Togo's", "brand_wikidata": "Q3530375"}
    sitemap_urls = ["https://locations.togos.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations\.togos\.com/[a-z]{2}/[a-z0-9-]+/[a-z0-9-]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        poi_js = response.xpath('//script[contains(., "W2GI.collection.poi")]/text()').get()
        if not poi_js:
            return
        poi = chompjs.parse_js_object(poi_js[poi_js.index("W2GI.collection.poi") :].split("=", 1)[1])[0]

        if poi.get("opening_status") != "open":
            return

        branch = poi.pop("name", None)
        item = DictParser.parse(poi)
        item["ref"] = item["website"] = response.url
        item["branch"] = branch or None
        item["street_address"] = merge_address_lines([poi.get("address1"), poi.get("address2")])
        item["phone"] = poi.get("phone")

        oh = OpeningHours()
        for index, day_hours in enumerate(chompjs.parse_js_object(poi["bho"])):
            if len(day_hours) != 2:
                continue
            open_time, close_time = day_hours
            if not open_time or not close_time or open_time == "9999" or close_time == "9999":
                continue
            oh.add_range(DAYS_FROM_SUNDAY[index], open_time, close_time, time_format="%H%M")
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)
        yield item
