import scrapy
from locations.brands import Brand
from locations.seo import extract_ldjson
from locations.spiders.sports_direct import SportsDirectSpider


class GameSpider(scrapy.spiders.SitemapSpider):
    name = "game"
    brand = Brand.from_wikidata('GAME', 'Q5519813')
    allowed_domains = ["storefinder.game.co.uk"]
    sitemap_urls = ["https://storefinder.game.co.uk/sitemap.xml"]
    sitemap_rules = [('/stores/', 'parse_store')]
    download_delay = 2
    custom_settings = {"DOWNLOAD_TIMEOUT": 10}

    def parse_store(self, response):
        for item in extract_ldjson(self.brand, response, "Store"):
            if item.has_geo():
                if "sportsdirect" in item['street_address'].lower().replace(' ', ''):
                    item.set_located_in(SportsDirectSpider.brand, self.logger)
                yield item
