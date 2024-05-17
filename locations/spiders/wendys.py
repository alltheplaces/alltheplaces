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
        item["opening_hours"] = self.clean_hours(response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]').first())
        item["opening_hours:drive_through"] = self.clean_hours(response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]').last())

        return item

    @staticmethod
    def clean_hours(hours_div):
        days = hours_div.xpath('.//@data-days').extract()
        days = json.loads(days)

        oh = OpeningHours()

        for day in days:
            day = day["day"]
            for interval in day["intervals"]:
                open_time = interval["start"]
                close_time = interval["end"]

                oh.add_range(day=day.titlecase()[:2], open_time=open_time, close_time=close_time)

        return oh.as_opening_hours()
