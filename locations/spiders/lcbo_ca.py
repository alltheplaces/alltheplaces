from json import loads
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_EN
from locations.items import Feature


class LcboCASpider(Spider):
    name = "lcbo_ca"
    item_attributes = {"brand": "LCBO", "brand_wikidata": "Q845263"}
    allowed_domains = ["www.lcbo.com", "www.google.com"]
    start_urls = ["https://www.google.com/maps/d/embed?mid=1yX0dX1020jTzQfMfIcYpdsxORg8"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Required for www.lcbo.com URLs

    def parse(self, response: Response) -> Iterable[Request]:
        # The start URL being an embedded Google Maps page created by LCBO is
        # listed at https://www.doingbusinesswithlcbo.com/content/dbwl/en/basepage/home/retail/StoreOpenings.html
        # and embeds within the page some basic store information, including
        # the store ID. We can take this store ID and use it to ask an LCBO
        # API to return more complete store data in JSON format.
        #
        # Note: This embedded Google Maps page has nothing to do with the
        # Google Maps API, despite the overloaded branding. LCBO have uploaded
        # location information and this is embedded within the page.
        # robots.txt on www.google.com allows these embedded map pages to be
        # crawled.
        js_blob = response.xpath('//script[contains(text(), "var _pageData = ")]/text()').get()
        js_blob = js_blob.split('var _pageData = "', 1)[1].split('";', 1)[0]
        if matches := re.findall(r'\[\[\\"Store\\",\[null,null,(\d+)\],', js_blob):
            for store_id in matches:
                yield Request(url=f"https://www.lcbo.com/en/storepickup/selection/store/?value={store_id}&st_loc_flag=true", headers={"X-Requested-With": "XMLHttpRequest"}, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        if not response.json()["success"]:
            # Store ID probably doesn't exist anymore and the embedded Google
            # Maps page linked from www.doingbusinesswithlcbo.com is probably
            # slightly out-of-date with the website.
            # At 2025-05-28, only 3 of 688 responses reached this code branch.
            return
        feature = response.json()["output"]
        item = DictParser.parse(feature)
        item["branch"] = item.pop("name", None)
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = "https://www.lcbo.com/en/stores/" + feature["url_key"]
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in loads(feature["schedule"]).items():
            if day_hours[f"{day_name}_status"] != "1":
                item["opening_hours"].set_closed(DAYS_EN[day_name.title()])
            else:
                day_start = day_hours["from"]["hours"] + ":" + day_hours["from"]["minutes"]
                day_end = day_hours["to"]["hours"] + ":" + day_hours["to"]["minutes"]
                break_start = day_hours["break_from"]["hours"] + ":" + day_hours["break_from"]["minutes"]
                break_end = day_hours["break_to"]["hours"] + ":" + day_hours["break_to"]["minutes"]
                if break_start == "00:00" and break_end == "00:00":
                    # No break in the day.
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], day_start, day_end)
                else:
                    # Day has a break in the middle.
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], day_start, break_start)
                    item["opening_hours"].add_range(DAYS_EN[day_name.title()], break_end, day_end)
        apply_category(Categories.SHOP_ALCOHOL, item)
        item["extras"]["alt_ref"] = feature["stloc_identifier"]
        yield item
