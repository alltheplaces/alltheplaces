from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class HollandAndBarrettSpider(SitemapSpider):
    name = "holland_and_barrett"
    item_attributes = {
        "brand": "Holland & Barrett",
        "brand_wikidata": "Q5880870",
    }
    sitemap_urls = ["https://www.hollandandbarrett.com/sitemap-stores.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.hollandandbarrett\.com\/stores\/([-\w]+)\/$",
            "parse",
        )
    ]

    def parse(self, response):
        yield LinkedDataParser.parse(response, "LocalBusiness")
