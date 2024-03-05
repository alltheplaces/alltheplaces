from scrapy.spiders import SitemapSpider

from locations.spiders.carpet_one_floor_and_home_us import CarpetOneFloorAndHomeUSSpider


class CarpetOneFloorAndHomeCASpider(SitemapSpider):
    name = "carpet_one_floor_and_home_ca"
    item_attributes = CarpetOneFloorAndHomeUSSpider.item_attributes
    allowed_domains = ["www.carpetone.ca"]
    sitemap_urls = ["https://www.carpetone.ca/locations-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.carpetone\.ca\/locations\/[^/]+/[^/]+$", "parse")]
    # Attempt crawling with a high delay to try and avoid receiving
    # truncated binary responses (non-HTTP). Possible rate limiting
    # mechanism to frustrate bots?
    download_delay = 10

    def parse(self, response):
        yield from CarpetOneFloorAndHomeUSSpider.parse_store(response)
