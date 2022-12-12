from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BelhavenPubsSpider(SitemapSpider):
    name = "belhaven_pubs"
    item_attributes = {
        "brand": "Belhaven Pubs",
        "brand_wikidata": "Q105516156",
        "country": "GB",
    }
    sitemap_urls = ["https://www.belhavenpubs.co.uk/xml-sitemap"]
    sitemap_rules = [(r"https:\/\/www\.belhavenpubs\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)\/$", "parse")]

    def parse(self, response):
        yield LinkedDataParser.parse(response, "BarOrPub")
