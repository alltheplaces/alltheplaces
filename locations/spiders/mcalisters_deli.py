import re
import urllib

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class McalistersDeliSpider(SitemapSpider, StructuredDataSpider):
    name = "mcalisters_deli"
    item_attributes = {"brand": "McAlister's Deli", "brand_wikidata": "Q17020829"}
    sitemap_urls = [
        "https://locations.mcalistersdeli.com/sitemap.xml",
    ]
    sitemap_follow = ["locations"]
    sitemap_rules = [(r"https://locations.mcalistersdeli.com/[a-z-]+/[a-z-]+/.*", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        data = urllib.parse.unquote_plus(response.xpath('//*[@type="module"]/text()').get())
        item["lat"], item["lon"] = re.search(r"latitude\":([0-9-\.]+),\"longitude\":([0-9-\.]+)}", data).groups()
        yield item
