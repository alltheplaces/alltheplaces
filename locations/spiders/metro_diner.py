from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class MetroDinerSpider(SitemapSpider, StructuredDataSpider):
    name = "metro_diner"
    item_attributes = {"brand": "Metro Diner", "brand_wikidata": "Q104870732"}
    allowed_domains = ["metrodiner.com"]
    sitemap_urls = ["https://metrodiner.com/locations-sitemap.xml"]
    wanted_types = ["Restaurant"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data):
        extract_google_position(item, response)

        yield item
