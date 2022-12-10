from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class HollandAndBarrettSpider(SitemapSpider):
    name = "holland_and_barrett"
    item_attributes = {
        "brand": "Holland & Barrett",
        "brand_wikidata": "Q5880870",
    }
    sitemap_urls = [
        "https://www.hollandandbarrett.com/sitemap-stores.xml",
        "https://www.hollandandbarrett.nl/sitemap-stores.xml",
        "https://www.hollandandbarrett.be/sitemap-stores.xml",
        "https://www.hollandandbarrett.ie/sitemap-stores.xml",
    ]
    sitemap_rules = [("/stores/", "parse"), ("/winkels/", "parse")]
    download_delay = 1.0

    def parse(self, response):
        item = LinkedDataParser.parse(response, "LocalBusiness")
        item["website"] = response.urljoin(item["website"])
        yield item
