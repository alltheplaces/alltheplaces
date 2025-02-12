import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, day_range
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

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["openingHours"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        # lat/lon are both parsed into lat, separate them
        (item["lat"], item["lon"]) = item["lat"]
        jsondata = json.loads(response.xpath('//input[@id="ctl00_mainContent_hidStoreJSON"]//@value').get())
        item["addr_full"] = jsondata["Address"]
        item["postcode"] = jsondata["PostCode"]
        item["phone"] = jsondata["Telephone"]

        try:
            item["opening_hours"] = self.parse_hours(jsondata["OpeningTimes"].split(", "))
        except:
            self.logger.error("Error parsing {}".format(jsondata["OpeningTimes"]))

        yield item

    def parse_hours(self, days):
        opening_hours = OpeningHours()

        for range in days:
            time_range, days = range.split(" ")
            if "-" in days:
                days = day_range(*days.split("-"))
            else:
                days = [days]

            if time_range == "Closed":
                opening_hours.set_closed(days)
            else:
                open_time, close_time = time_range.split("-")
                opening_hours.add_days_range(days, open_time, close_time, "%H.%M")

        return opening_hours
