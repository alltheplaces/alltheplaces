from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CircleKSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    allowed_domains = ["www.circlek.com"]
    start_urls = ["https://www.circlek.com/list-united-states-stores?lang=en"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    rules = [Rule(LinkExtractor(allow="/store-locator/"), callback="parse_sd")]
    wanted_types = ["ConvenienceStore"]

    def inspect_item(self, item, response):
        days = response.xpath('//div[contains(@class,"hours-item")]')
        oh = OpeningHours()
        for day in days:
            hours = day.xpath("./span[2]/text()").get().strip("\n").strip()
            oh.add_range(
                day=day.xpath("./span[1]/text()").get().strip(),
                open_time="12:00 AM" if hours == "Open 24h" else hours.split(" to ")[0],
                close_time="12:00 AM" if hours == "Open 24h" else hours.split(" to ")[1],
                time_format="%I:%M %p",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
