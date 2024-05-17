import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class WendysSpider(SitemapSpider, StructuredDataSpider):
    name = "wendys"
    item_attributes = {"brand": "Wendy's", "brand_wikidata": "Q550258"}
    wanted_types = ["FastFoodRestaurant"]
    sitemap_urls = ["https://locations.wendys.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.wendys.com/.+/\w\w/.+/.+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = ld_data.get("url")

        # Opening hours for the drive-through seem to get included with regular hours, so clean that up
        opening_hours_divs = response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]')
        item["opening_hours"] = self.clean_hours(opening_hours_divs[0])

        if len(opening_hours_divs) > 1:
            item["extras"]["opening_hours:drive_through"] = self.clean_hours(opening_hours_divs[1])

        if breakfast_hours_divs := response.xpath(
            '//div[@class="LocationInfo-breakfastInfo js-breakfastInfo"]/span[@class="c-location-hours-today js-location-hours"]'
        ):
            item["extras"]["breakfast"] = self.clean_hours(breakfast_hours_divs[0])

        yield item

    @staticmethod
    def clean_hours(hours_div):
        days = hours_div.xpath(".//@data-days").extract_first()
        days = json.loads(days)

        oh = OpeningHours()

        for day in days:
            for interval in day["intervals"]:
                # These interval ranges are 24 hour times represented as integers, so they need to be converted to strings
                open_time = str(interval["start"]).zfill(4)
                close_time = str(interval["end"]).zfill(4)

                oh.add_range(day=day["day"].title()[:2], open_time=open_time, close_time=close_time, time_format="%H%M")

        return oh.as_opening_hours()
