from re import search
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GreatWolfResortsUS(SitemapSpider, StructuredDataSpider):
    name = "great_wolf_resorts_us"
    item_attributes = {"brand": " Great Wolf Resorts", "brand_wikidata": "Q5600260"}
    allowed_domains = ["www.greatwolf.com"]
    sitemap_urls = ["https://www.greatwolf.com/php-root.sitemap.xml"]
    sitemap_rules = [(r"/customer-service$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("facebook")
        item.pop("image")
        item.pop("twitter")
        has_map = unquote(ld_data["hasMap"])
        item["lat"], item["lon"] = search(r"[@=](-?\d+\.\d+),(-?\d+\.\d+)", has_map).groups()

        yield item
