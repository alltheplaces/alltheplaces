from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class CircleKSESpider(SitemapSpider, StructuredDataSpider):
    name = "circle_k_se"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    sitemap_urls = ["https://www.circlek.se/stations/sitemap.xml"]
    sitemap_rules = [("/station/circle-k-", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("172.16.34.158", "www.circlek.se")
            yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
