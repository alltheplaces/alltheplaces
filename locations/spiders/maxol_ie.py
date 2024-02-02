import html
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class MaxolIESpider(SitemapSpider, StructuredDataSpider):
    name = "maxol_ie"
    item_attributes = {"brand": "Maxol", "brand_wikidata": "Q3302837", "extras": Categories.FUEL_STATION.value}
    sitemap_urls = ["https://stations.maxol.ie/sitemap.xml"]
    sitemap_rules = [(r"\.ie\/[-\w]+\/[-.\w]+\/[-\/\w]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = html.unescape(item["name"])
        item["street_address"] = html.unescape(item["street_address"])

        if m := re.search(r"\"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
