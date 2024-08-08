import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaBESpider(SitemapSpider):
    name = "dominos_pizza_be"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.be"]
    sitemap_urls = ["https://www.dominos.be/sitemap.aspx"]
    url_regex = r"https:\/\/www\.dominos\.be/nl/winkel\/([\w]+)-([\w]+)-([\d]+)$"
    sitemap_rules = [(url_regex, "parse_store")]
    start_urls = ("https://www.dominos.be/winkels",)
    user_agent = BROWSER_DEFAULT

    def parse_store(self, response):
        match = re.match(self.url_regex, response.url)
        ref = match.group(3)
        country = match.group(1)
        address_data = response.xpath('//a[@id="open-map-address"]/text()').extract()
        locality_data = re.search(r"(.*) ([A-Z]{2}) (.*)", address_data[1].strip())
        properties = {
            "ref": ref.strip("/"),
            "name": response.xpath('//h1[@class="storetitle"]/text()').extract_first(),
            "street_address": address_data[0].strip().strip(","),
            "country": country,
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "website": response.url,
        }
        if locality_data:
            properties["city"] = locality_data.group(1)
            properties["postcode"] = locality_data.group(3)
        yield Feature(**properties)
