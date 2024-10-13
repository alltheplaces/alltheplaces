import json

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class ShoeZoneGBSpider(SitemapSpider, StructuredDataSpider):
    name = "shoe_zone_gb"
    item_attributes = {
        "brand": "Shoe Zone",
        "brand_wikidata": "Q7500016",
        "country": "GB",
    }
    sitemap_urls = ["https://www.shoezone.com/sitemap_stores.xml"]
    sitemap_rules = [(r"https:\/\/www\.shoezone\.com\/Stores\/[-._\w]+-(\d+)$", "parse_sd")]
    wanted_types = ["ShoeStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # lat/lon are both parsed into lat, separate them
        (item["lat"], item["lon"]) = item["lat"]
        jsondata = json.loads(response.xpath('//input[@id="ctl00_mainContent_hidStoreJSON"]//@value').get())
        item["addr_full"] = jsondata["Address"]
        item["postcode"] = jsondata["PostCode"]
        item["phone"] = jsondata["Telephone"]

        item["opening_hours"] = self.parse_hours(jsondata["OpeningTimes"].split(", "))
        yield item

    def parse_hours(self, days):
        opening_hours = OpeningHours()

        for range in days:
            time_range, day_range = range.split(" ")
            open_time, close_time = time_range.split("-")
            open_hour, open_minute = open_time.split(".")
            close_hour, close_minute = close_time.split(".")

            if "-" in day_range:
                start_day, end_day = day_range.split("-")
                for day in DAYS_3_LETTERS[DAYS_3_LETTERS.index(start_day) : DAYS_3_LETTERS.index(end_day) + 1]:
                    opening_hours.add_range(
                        day[0:2],
                        "{}:{}".format(open_hour, open_minute),
                        "{}:{}".format(close_hour, close_minute),
                    )

            else:
                opening_hours.add_range(
                    day_range[0:2],
                    "{}:{}".format(open_hour, open_minute),
                    "{}:{}".format(close_hour, close_minute),
                )
        return opening_hours.as_opening_hours()
