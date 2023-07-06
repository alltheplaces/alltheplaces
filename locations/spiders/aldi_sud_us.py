from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AldiSudUSSpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_us"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171672", "country": "US"}
    allowed_domains = ["stores.aldi.us"]
    sitemap_urls = ["https://stores.aldi.us/robots.txt"]
    sitemap_rules = [
        (r"^https://stores\.aldi\.us/.*/.*/.*$", "parse"),
    ]
    wanted_types = ["GroceryStore"]

    def parse(self, response):
        for city in response.css('[itemprop="address"] .Address-city'):
            city.root.set("itemprop", "addressLocality")
        yield from self.parse_sd(response)
