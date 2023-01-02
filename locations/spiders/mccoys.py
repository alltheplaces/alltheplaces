from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class McCoysSpider(SitemapSpider, StructuredDataSpider):
    name = "mccoys"
    item_attributes = {"brand": "McCoy's Building Supply", "brand_wikidata": "Q27877295"}
    allowed_domains = ["www.mccoys.com"]
    sitemap_urls = ["https://www.mccoys.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse_sd")]
    wanted_types = ["Store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%-I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()

        yield item
