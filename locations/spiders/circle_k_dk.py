from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class CircleKDKSpider(SitemapSpider, StructuredDataSpider):
    name = "circle_k_dk"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    sitemap_urls = ["https://www.circlek.dk/stations/sitemap.xml"]
    sitemap_rules = [("/station/circle-k-", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        apply_category(Categories.FUEL_STATION, item)
        yield item
