from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BuckleSpider(SitemapSpider, StructuredDataSpider):
    name = "buckle"
    item_attributes = {
        "brand": "Buckle",
        "brand_wikidata": "Q4983306",
    }

    allowed_domains = ["local.buckle.com"]
    sitemap_urls = [
        "https://local.buckle.com/robots.txt",
    ]
    sitemap_rules = [(r"https://local\.buckle\.com/.*\d/", "parse")]
    json_parser = "json5"


    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
