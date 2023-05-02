import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class TacobellSpider(scrapy.spiders.SitemapSpider):
    name = "tacobell"
    item_attributes = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}
    sitemap_urls = [
        "https://locations.tacobell.com/sitemap.xml",
        "https://locations.tacobell.ca/sitemap.xml",
        "https://locations.tacobell.co.uk/sitemap.xml",
        # TODO: Different scheme to above, perhaps another spider?
        # "https://tacobell.es/restaurantes-sitemap.xml",
        # "https://tacobell.nl/location-sitemap.xml",
    ]

    def _parse_sitemap(self, response):
        def follow_link(url):
            for s in [
                "restaurant.html",
                "mexican-food.html",
                "breakfast.html",
                "dinner.html",
                "drive-thru.html",
                "fast-food.html",
                "lunch.html",
                "delivery.html",
                "take-out.html",
            ]:
                if url.endswith(s):
                    return False
            if "tacobell.ca/fr/" in url:
                return False
            return True

        for x in super()._parse_sitemap(response):
            if follow_link(x.url):
                yield x

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        if item := LinkedDataParser.parse(response, "FastFoodRestaurant"):
            if "locations.tacobell.ca" in item["website"]:
                item["country"] = "CA"
            yield item
