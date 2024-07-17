from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AwRestaurantsSpider(SitemapSpider, StructuredDataSpider):
    name = "aw_restaurants"
    item_attributes = {"brand": "A&W Restaurants", "brand_wikidata": "Q277641"}
    allowed_domains = ["awrestaurants.com"]
    sitemap_urls = ["https://awrestaurants.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]
    time_format = "%H:%M:%S"

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("http://awdev.dev.wwbtc.com/", "https://awrestaurants.com/")
            yield entry
