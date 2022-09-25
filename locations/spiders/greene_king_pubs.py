from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class GreeneKingPubsSpider(SitemapSpider):
    name = "greene_king_pubs"
    item_attributes = {
        "brand": "Greene King",
        "brand_wikidata": "Q5564162",
        "country": "GB",
    }
    sitemap_urls = ["https://www.greeneking-pubs.co.uk/xml-sitemap/"]
    sitemap_rules = [
        (
            r"https:\/\/www\.greeneking-pubs\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)\/$",
            "parse",
        )
    ]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response):
        yield LinkedDataParser.parse(response, "BarOrPub")
