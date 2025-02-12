from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DennysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dennys_us"
    item_attributes = {"brand": "Denny's", "brand_wikidata": "Q1189695"}
    sitemap_urls = ["https://locations.dennys.com/robots.txt"]
    sitemap_rules = [(r"https://locations.dennys.com/[^/]+/[^/]+/\d+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None
        item["opening_hours"] = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            day = day_time["dayOfWeek"].split("/")[-1]
            time = day_time["opens"]
            if "Open 24 Hours" in time.strip():
                item["opening_hours"].add_range(day, "00:00", "23:59")
            elif "Closed" in time:
                item["opening_hours"].set_closed(day)
            else:
                open_time, close_time = time.split("  to  ")
                item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), "%I:%M %p")

        yield item
