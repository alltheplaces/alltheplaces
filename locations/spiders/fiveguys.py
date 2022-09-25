# -*- coding: utf-8 -*-
import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FiveguysSpider(scrapy.spiders.SitemapSpider):
    name = "fiveguys"
    item_attributes = {"brand": "Five Guys", "brand_wikidata": "Q1131810"}
    sitemap_urls = [
        "https://restaurants.fiveguys.com/sitemap.xml",
        "https://restaurants.fiveguys.ae/sitemap.xml",
        "https://restaurants.fiveguys.be/sitemap.xml",
        "https://restaurants.fiveguys.ca/sitemap.xml",
        "https://restaurants.fiveguys.ch/sitemap.xml",
        "https://restaurants.fiveguys.cn/sitemap.xml",
        "https://restaurants.fiveguys.de/sitemap.xml",
        "https://restaurantes.fiveguys.es/sitemap.xml",
        "https://restaurants.fiveguys.fr/sitemap.xml",
        "https://restaurants.fiveguys.ie/sitemap.xml",
        "https://restaurants.fiveguys.com.kw/sitemap.xml",
        "https://restaurants.fiveguys.it/sitemap.xml",
        "https://restaurants.fiveguys.lu/sitemap.xml",
        "https://restaurants.fiveguys.my/sitemap.xml",
        "https://restaurants.fiveguys.nl/sitemap.xml",
        "https://restaurants.fiveguys.qa/sitemap.xml",
        "https://restaurants.fiveguys.sa/sitemap.xml",
        "https://restaurants.fiveguys.sg/sitemap.xml",
        "https://restaurants.fiveguys.co.uk/sitemap.xml",
    ]
    download_delay = 0.5

    def _parse_sitemap(self, response):
        for x in super()._parse_sitemap(response):
            # Brittle, but hey saves on GET requests, all site pages presently have a hyphen in the URL
            if "-" in x.url:
                yield x

    def parse(self, response):
        # How do you like your duplicates served?
        # Prefer English, but some estates are only native language.
        lang = response.xpath("/html/@lang").get().lower()
        is_a_keeper = lang.startswith("en")
        for s in ["guys.fr/", "guys.es/", "guys.de/"]:
            if s in response.url:
                is_a_keeper = True
        if is_a_keeper:
            MicrodataParser.convert_to_json_ld(response)
            yield LinkedDataParser.parse(response, "FastFoodRestaurant")
