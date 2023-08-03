import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CvsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cvs_us"
    item_attributes = {"brand": "CVS", "brand_wikidata": "Q2078880"}
    allowed_domains = ["www.cvs.com"]
    sitemap_urls = ["https://www.cvs.com/sitemap/store-details.xml"]

    def parse(self, response):
        if response.css("link[rel~=canonical]").attrib["href"] == "https://www.cvs.comundefined":
            # Weird garbage, seemingly for closed locations
            return
        yield from super().parse(response)

    def post_process_item(self, item, response, ld_data, **kwargs):
        data = json.loads(response.xpath("//@sd-props").get())
        storeInfo = data["cvsStoreDetails"]["storeInfo"]
        item["lat"] = storeInfo["latitude"]
        item["lon"] = storeInfo["longitude"]
        item["ref"] = storeInfo["storeId"]

        # OSM generally wants to model a separate node for the shop, pharmacy,
        # and clinic; this data is a little too messy for that, so just collect
        # the store's distinguishing attributes as properties on a single feature.
        item["extras"]["departments"] = storeInfo["identifier"]
        item["extras"]["store_type"] = data["cvsStoreTypeImage"]["altText"]

        hours = {
            f'opening_hours:{dept["name"]}': self.parse_hours(dept["regHours"])
            for dept in data["cvsStoreDetails"]["hours"]["departments"]
        }
        item["extras"].update(hours)

        # Most stores have retail, with the exception of those located inside
        # Target, or bad data. We've defined specific opening_hours above; pick
        # one and promote it to the unqualified key.
        if default := hours.get("opening_hours:retail") or hours.get("opening_hours:pharmacy"):
            item["opening_hours"] = default

        yield item

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for row in hours:
            if row["startTime"] == "Open 24 Hours":
                row["startTime"] = "12:00 AM"
            if row["endTime"] == "Open 24 Hours":
                row["endTime"] = "11:59 PM"

            if {"breakStart", "breakEnd"} <= row.keys():
                intervals = [
                    (row["startTime"], row["breakStart"]),
                    (row["breakEnd"], row["endTime"]),
                ]
            else:
                intervals = [
                    (row["startTime"], row["endTime"]),
                ]
            for open_time, close_time in intervals:
                opening_hours.add_range(row["weekday"], open_time, close_time, "%I:%M %p")
        return opening_hours.as_opening_hours()
