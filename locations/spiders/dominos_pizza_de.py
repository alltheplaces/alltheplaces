import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaDESpider(SitemapSpider):
    name = "dominos_pizza_de"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.de"]
    sitemap_urls = ["https://www.dominos.de/sitemap.aspx"]
    url_regex = r"https:\/\/www\.dominos\.de\/filiale\/([\w]+)-([\w]+)-([\d]+)$"
    sitemap_rules = [(url_regex, "parse_store")]
    user_agent = BROWSER_DEFAULT

    def parse_store(self, response):
        match = re.match(self.url_regex, response.url)
        ref = match.group(3)
        country = match.group(1)
        address_data = response.xpath('//a[@id="open-map-address"]/text()').extract()
        properties = {
            "ref": ref,
            "name": response.xpath('//h1[@class="storetitle"]/text()').extract_first(),
            "street_address": clean_address(address_data[0].strip().strip(",")),
            "country": country,
            "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
            "website": response.url,
        }
        if locality_data := re.match(r"([\d]+)? ?([-\ \w'À-Ÿ()]+)$", address_data[1].strip()):
            properties["city"] = locality_data.group(2)
            properties["postcode"] = locality_data.group(1)

        yield Feature(**properties)
