from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class MetroDinerUSSpider(SitemapSpider, StructuredDataSpider):
    name = "metro_diner_us"
    item_attributes = {"brand": "Metro Diner", "brand_wikidata": "Q104870732"}
    sitemap_urls = ["https://metrodiner.com/locations-sitemap.xml"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        yield item
