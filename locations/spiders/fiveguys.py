import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FiveguysSpider(scrapy.spiders.SitemapSpider):
    name = "fiveguys"
    item_attributes = {
        "brand": "Five Guys",
        "brand_wikidata": "Q1131810",
    }
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
    sitemap_follow = [
        r"^https://restaurants\.fiveguys\.com\/[^/]+$",
        r"^https://restaurants\.fiveguys\.ae\/en_ae\/[^/]+$",
        r"^https://restaurants\.fiveguys\.be\/en_be\/[^/]+$",
        r"^https://restaurants\.fiveguys\.ca\/[^/]+$",
        r"^https://restaurants\.fiveguys\.ch\/en_ch\/[^/]+$",
        r"^https://restaurants\.fiveguys\.cn\/en\/[^/]+$",
        r"^https://restaurants\.fiveguys\.de\/[^/]+\/[^/]+$",
        r"^https://restaurants\.fiveguys\.es\/[^/]+\/[^/]+$",
        r"^https://restaurants\.fiveguys\.fr\/[^/]+\/[^/]+$",
        r"^https://restaurants\.fiveguys\.ie\/[^/]+$",
        r"^https://restaurants\.fiveguys\.com\.kw\/en_kw\/[^/]+$",
        r"^https://restaurants\.fiveguys\.it\/en_it\/[^/]+$",
        r"^https://restaurants\.fiveguys\.lu\/en_lu\/[^/]+$",
        r"^https://restaurants\.fiveguys\.my\/en\/[^/]+$",
        r"^https://restaurants\.fiveguys\.nl\/en_nl\/[^/]+$",
        r"^https://restaurants\.fiveguys\.qa\/en_qa\/[^/]+$",
        r"^https://restaurants\.fiveguys\.sa\/en_sa\/[^/]+$",
        r"^https://restaurants\.fiveguys\.sg\/[^/]+$",
        r"^https://restaurants\.fiveguys\.co\.uk\/.+$",
    ]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        yield LinkedDataParser.parse(response, "FastFoodRestaurant")
