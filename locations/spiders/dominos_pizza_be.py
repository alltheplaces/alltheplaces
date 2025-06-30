from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaBESpider(SitemapSpider):
    name = "dominos_pizza_be"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.be"]
    sitemap_urls = ["https://www.dominos.be/sitemap.aspx"]
    sitemap_rules = [(r"/nl/winkel//?[^/]+\d+$", "parse_store")]
    user_agent = BROWSER_DEFAULT

    def parse_store(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[@class="storetitle"]/text()').extract_first(),
            "street_address": response.xpath('//a[@id="open-map-address"]/text()').get(),
            "addr_full": response.xpath('//a[@id="open-map-address"]').xpath("normalize-space()").extract(),
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "website": response.url,
        }
        yield Feature(**properties)
