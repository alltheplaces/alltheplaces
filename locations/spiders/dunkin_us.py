import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.dunkin_at import DUNKIN_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class DunkinUSSpider(SitemapSpider):
    name = "dunkin_us"
    item_attributes = DUNKIN_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.dunkindonuts.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.dunkindonuts.com/locations/us/[^/]+/[^/]+/[^/]+/[^/]+/$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response):
        location_data = DictParser.get_nested_key(
            json.loads(response.xpath('//*[@id="__NEXT_DATA__"]//text()').get()), "initialLocationDetails"
        )
        location_data.update(location_data.pop("contactDetails"))
        location_data.update(location_data.pop("geoDetails"))
        item = DictParser.parse(location_data)
        item["housenumber"] = location_data.get("address").get("line2")
        oh = OpeningHours()
        for day_time in location_data.get("locationHours"):
            day = day_time.get("dayOfWeek")
            open_time = day_time.get("startTime")
            close_time = day_time.get("endTime")
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        # extra_features = filter(None, [feature.get("name") for feature in location_data.get("amenities")])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in location_data.get("amenities"), False)
        apply_yes_no(Extras.WIFI, item, "WiFi" in location_data.get("amenities"), False)
        yield item
