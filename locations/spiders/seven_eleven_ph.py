import scrapy
from scrapy import Selector
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_EN, OpeningHours
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenPhSpider(scrapy.Spider):
    name = "seven_eleven_ph"
    allowed_domains = ["www.7-eleven.com.ph"]
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES

    def start_requests(self):
        for city in city_locations("PH"):
            lat = city.get("latitude")
            lon = city.get("longitude")
            yield JsonRequest(
                f"https://www.7-eleven.com.ph/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results=100&search_radius=500&filter=62",
            )

    def parse(self, response: Response):
        for poi in response.json():
            item = DictParser.parse(poi)
            item["branch"] = poi.get("store")
            self.parse_hours(item, poi)
            if "[PERMANENT CLOSED]" in item["addr_full"]:
                item["extras"]["end_date"] = "yes"
            self.clean_address(item)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item

    def parse_hours(self, item, poi):
        hours = poi.get("hours")
        if not hours:
            return
        try:
            days = Selector(text=hours).xpath("//tr")
            oh = OpeningHours()
            for day in days:
                day_name = day.xpath("td[1]/text()").get()
                times = day.xpath("td[2]/time/text()").get()
                if not day_name or not times:
                    continue
                if "Closed" in times:
                    continue
                open_time, close_time = times.split(" - ")
                oh.add_range(DAYS_EN.get(day_name), open_time, close_time, "%I:%M %p")
            item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Error parsing hours: {e}", exc_info=True)
            self.crawler.stats.inc_value("atp/hours/failed")

    def clean_address(self, item):
        for term in ["[OPEN]", "[TEMPORARY CLOSED]", "[PERMANENT CLOSED]"]:
            if term in item["addr_full"]:
                item["addr_full"] = item["addr_full"].replace(term, "").strip()
                break
