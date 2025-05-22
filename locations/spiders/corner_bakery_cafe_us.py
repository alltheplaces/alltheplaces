from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CornerBakeryCafeUSSpider(CrawlSpider, StructuredDataSpider):
    name = "corner_bakery_cafe_us"
    item_attributes = {"brand": "Corner Bakery", "brand_wikidata": "Q5171598"}
    allowed_domains = ["cornerbakerycafe.com"]
    start_urls = [
        "https://cornerbakerycafe.com/locations/all",
    ]
    rules = [Rule(LinkExtractor(allow=r"/location/[-\w]+/?$"), callback="parse_sd")]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            days, times = hour.split(" ")
            open_hour, close_hour = times.split("-")
            if len(days) > 2:
                day = days.split(",")
                for d in day:
                    opening_hours.add_range(
                        day=d,
                        open_time=open_hour,
                        close_time=close_hour,
                        time_format="%H:%M",
                    )
            else:
                opening_hours.add_range(
                    day=days,
                    open_time=open_hour,
                    close_time=close_hour,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def post_process_item(self, item, response, ld_data):
        item["ref"] = response.url

        try:
            hours = self.parse_hours(ld_data["openingHours"])
            if hours:
                item["opening_hours"] = hours
        except:
            pass

        yield item
