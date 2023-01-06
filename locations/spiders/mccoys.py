import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class McCoysSpider(SitemapSpider, StructuredDataSpider):
    name = "mccoys"
    item_attributes = {
        "brand": "McCoy's Building Supply",
        "brand_wikidata": "Q27877295",
    }
    allowed_domains = ["www.mccoys.com"]
    sitemap_urls = ["https://www.mccoys.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse_sd")]
    wanted_types = ["Store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()[contains(.,\'"Store"\')]').get())
        oh = OpeningHours()
        for day in data.get("OpeningHoursSpecification"):
            if day.get("opens") == "Closed":
                continue
            oh.add_range(
                day=day.get("dayOfWeek"),
                open_time=day.get("opens"),
                close_time=day.get("closes"),
                time_format="%I:%M %p",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
