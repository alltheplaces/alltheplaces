import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class JohnLewisGBSpider(SitemapSpider, StructuredDataSpider):
    name = "john_lewis_gb"
    item_attributes = {"brand": "John Lewis", "brand_wikidata": "Q1918981"}
    sitemap_urls = ["https://www.johnlewis.com/shops-services.xml"]
    sitemap_rules = [("/our-shops/", "parse_sd")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None
        item["website"] = response.url
        if m := re.search(r"latitude%22%3A(-?\d+\.\d+)%2C%22longitude%22%3A(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
