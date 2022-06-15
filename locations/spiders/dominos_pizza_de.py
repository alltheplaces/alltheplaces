# -*- coding: utf-8 -*-
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class DomionsPizzaGermanySpider(SitemapSpider):
    name = "dominos_pizza_de"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.de"]
    sitemap_urls = ["https://www.dominos.de/sitemap.aspx"]
    url_regex = r"https:\/\/www\.dominos\.de\/filiale\/([\w]+)-([\w]+)-([\d]+)$"
    sitemap_rules = [(url_regex, "parse_store")]

    def parse_store(self, response):
        match = re.match(self.url_regex, response.url)
        ref = match.group(3)
        country = match.group(1)
        address_data = response.xpath('//a[@id="open-map-address"]/text()').extract()
        locality_data = address_data[1].strip()
        properties = {
            "ref": ref,
            "name": response.xpath('//h1[@class="storetitle"]/text()').extract_first(),
            "street_address": address_data[0].strip().strip(","),
            "city": re.search(r"(.*) (.*[A-Za-z])", locality_data).group(2),
            "postcode": re.search(r"(.*) (.*[A-Za-z])", locality_data).group(1),
            "country": country,
            "lat": response.xpath('//input[@id="store-lat"]/@value')
            .get()
            .replace(",", "."),
            "lon": response.xpath('//input[@id="store-lon"]/@value')
            .get()
            .replace(",", "."),
            "website": response.url,
        }
        yield GeojsonPointItem(**properties)
