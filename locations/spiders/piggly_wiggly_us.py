import json
import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class PigglyWigglyUSSpider(SitemapSpider):
    name = "piggly_wiggly_us"
    item_attributes = {"brand": "Piggly Wiggly", "brand_wikidata": "Q3388303"}
    sitemap_urls = ["https://www.pigglywiggly.com/wp-sitemap-posts-page-1.xml"]
    sitemap_rules = [(r"/store-locations/.+/", "parse")]

    def parse(self, response, **kwargs):
        locations = json.loads(re.search(r"locations = (\[?{.+}\]?);", response.text).group(1))
        if isinstance(locations, dict):
            locations = locations.values()

        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["website"] = item.pop("email")
            item["name"] = None
            yield item
