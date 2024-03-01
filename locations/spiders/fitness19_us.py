import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class Fitness19USSpider(SitemapSpider, StructuredDataSpider):
    name = "fitness19_us"
    item_attributes = {"brand": "Fitness 19", "brand_wikidata": "Q121787953", "extras": Categories.GYM.value}
    sitemap_urls = ["https://www.fitness19.com/location-sitemap.xml"]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"LatLng\((-?\d+\.\d+) ,(-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
