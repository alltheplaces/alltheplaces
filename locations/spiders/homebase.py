from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class Homebase(SitemapSpider, StructuredDataSpider):
    name = "homebase"
    item_attributes = {"brand": "Homebase", "brand_wikidata": "Q9293447"}
    sitemap_urls = ["https://store.homebase.co.uk/robots.txt"]
    sitemap_rules = [
        (r"https:\/\/store\.homebase\.co\.uk\/[-\w]+\/[-.\w]+$", "parse_sd")
    ]
    wanted_types = ["HardwareStore"]
