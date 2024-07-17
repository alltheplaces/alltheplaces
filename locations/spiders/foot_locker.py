import scrapy

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class FootLockerSpider(scrapy.spiders.SitemapSpider):
    name = "foot_locker"
    item_attributes = {"brand": "Foot Locker", "brand_wikidata": "Q63335"}
    sitemap_urls = [
        "https://stores.footlocker.com/sitemap.xml",
        "https://stores.footlocker.at/sitemap.xml",
        "https://stores.footlocker.be/sitemap.xml",
        "https://stores.footlocker.ca/sitemap.xml",
        "https://stores.footlocker.cz/sitemap.xml",
        "https://stores.footlocker.de/sitemap.xml",
        "https://stores.footlocker.dk/sitemap.xml",
        "https://stores.footlocker.es/sitemap.xml",
        "https://stores.footlocker.fr/sitemap.xml",
        "https://stores.footlocker.gr/sitemap.xml",
        "https://stores.footlocker.hu/sitemap.xml",
        "https://stores.footlocker.ie/sitemap.xml",
        "https://stores.footlocker.it/sitemap.xml",
        "https://stores.footlocker.lu/sitemap.xml",
        "https://stores.footlocker.nl/sitemap.xml",
        "https://stores.footlocker.no/sitemap.xml",
        "https://stores.footlocker.co.nz/sitemap.xml",
        "https://stores.footlocker.pl/sitemap.xml",
        "https://stores.footlocker.pt/sitemap.xml",
        "https://stores.footlocker.se/sitemap.xml",
        "https://stores.footlocker.co.uk/sitemap.xml",
    ]
    sitemap_rules = [
        ("/en/", "parse"),
        (".co.uk/", "parse"),
        (".co.nz/", "parse"),
        (".com/", "parse"),
        (".ie/", "parse"),
    ]
    download_delay = 0.5

    def parse(self, response):
        item = LinkedDataParser.parse(response, "ShoeStore")
        if item:
            item["ref"] = response.url

            if "stores.footlocker.com" in response.url:
                item["country"] = "US"
                # Other countries are handled by the TLD in pipeline code
            apply_category(Categories.SHOP_SHOES, item)

            yield item
