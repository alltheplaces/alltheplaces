from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MetroDinerSpider(SitemapSpider, StructuredDataSpider):
    name = "metrodiner"
    item_attributes = {"brand": "Metro Diner", "brand_wikidata": "Q104870732"}
    allowed_domains = ["metrodiner.com"]
    sitemap_urls = ["https://metrodiner.com/locations-sitemap.xml"]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data):
        oh = OpeningHours()
        oh.from_linked_data(ld_data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()

        extract_google_position(item, response)

        yield item
