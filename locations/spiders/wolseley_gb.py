from scrapy.spiders import SitemapSpider

from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class WolseleyGB(SitemapSpider, StructuredDataSpider):
    name = "wolseley_gb"
    item_attributes = {"brand": "Wolseley", "brand_wikidata": "Q8030423"}
    sitemap_urls = ["https://www.wolseley.co.uk/sitemap.xml"]
    sitemap_rules = [
        (f"https:\/\/www\.wolseley\.co\.uk\/branch\/[-\w]+\/$", "parse_sd")
    ]
    wanted_types = ["LocalBusiness"]
    download_delay = 5

    def inspect_item(self, item, response):
        item["street_address"] = clean_address(item["street_address"])

        yield item
