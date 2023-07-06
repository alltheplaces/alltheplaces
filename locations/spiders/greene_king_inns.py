from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.linked_data_parser import LinkedDataParser


class GreeneKingInnsSpider(SitemapSpider):
    name = "greene_king_inns"
    item_attributes = {
        "brand": "Greene King Inns",
        "brand_wikidata": "Q5564162",
        "country": "GB",
        "extras": Categories.HOTEL.value,
    }
    sitemap_urls = ["https://www.greenekinginns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.greenekinginns\.co\.uk\/hotels\/([-\w]+)\/$", "parse")]

    def parse(self, response):
        item = LinkedDataParser.parse(response, "Hotel")

        if item is None:
            return

        item["ref"] = response.url

        return item
