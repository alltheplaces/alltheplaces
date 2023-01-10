import html

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CircleKSpider(CrawlSpider, StructuredDataSpider):
    name = "circle_k"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010", "country": "US"}
    allowed_domains = ["www.circlek.com"]
    start_urls = ["https://www.circlek.com/list-united-states-stores?lang=en"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    rules = [Rule(LinkExtractor(allow="/store-locator/"), callback="parse_sd")]
    wanted_types = ["ConvenienceStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
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

        item["name"] = html.unescape(item["name"])

        if "Convenience Store" in item["name"]:
            apply_category(Categories.SHOP_CONVENIENCE, item)
        if "Gas Station" in item["name"]:
            apply_category(Categories.FUEL_STATION, item)

        yield item
