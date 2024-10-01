from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BurgervilleSpider(SitemapSpider):
    name = "burgerville"
    item_attributes = {"brand": "Burgerville", "brand_wikidata": "Q4998570"}
    allowed_domains = ["locations.burgerville.com"]
    sitemap_urls = ["https://locations.burgerville.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations.burgerville.com\/burgerville-.*",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")

        if item is None:
            return
        item["country"] = "US"
        yield item
    drop_attributes = {"image"}
