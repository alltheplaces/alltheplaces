import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OliveGardenSpider(SitemapSpider):
    name = "olive_garden"
    item_attributes = {"brand": "Olive Garden", "brand_wikidata": "Q3045312"}
    allowed_domains = ["olivegarden.com"]
    sitemap_urls = [
        "https://www.olivegarden.com/en-locations-sitemap.xml",
    ]
    sitemap_rules = [(r"[0-9]+$", "parse")]
    requires_proxy = True

    def _parse_sitemap(self, response):
        for row in super()._parse_sitemap(response):
            store_id = re.findall(r"[0-9]+$", row.url)[0]
            url = f"https://www.olivegarden.com/web-api/restaurant/{store_id}?locale=en_US&restNumFlag=true&restaurantNumber={store_id}"
            yield scrapy.Request(
                url=url, callback=self.parse_store, cb_kwargs={"store_id": store_id, "website": row.url}
            )

    def parse_store(self, response, store_id, website):
        data = response.json().get("successResponse", {}).get("restaurantDetails", {})
        item = DictParser.parse(data.get("address"))
        item["ref"] = store_id
        item["name"] = data.get("restaurantName")
        item["phone"] = data.get("restPhoneNumber")[0].get("Phone")
        if lat_lon_txt := data.get("address", {}).get("longitudeLatitude"):
            item["lat"], item["lon"] = lat_lon_txt.split(",")
        item["website"] = website
        days = [day for day in data.get("weeklyHours") if day.get("hourCode") == "OP"]
        oh = OpeningHours()
        for day in days:
            oh.add_range(
                day=DAYS[day.get("dayOfWeek") - 1],
                open_time=day.get("startTime"),
                close_time=day.get("endTime"),
                time_format="%I:%M%p",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
