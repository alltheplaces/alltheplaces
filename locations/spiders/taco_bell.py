from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser

TACO_BELL_SHARED_ATTRIBUTES = {"brand": "Taco Bell", "brand_wikidata": "Q752941"}


class TacoBellSpider(SitemapSpider):
    name = "taco_bell"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    TACOBELL_CANTINA = {"name": "Taco Bell Cantina", "brand_wikidata": "Q111972226"}
    sitemap_urls = [
        "https://locations.tacobell.com/sitemap.xml",
        "https://locations.tacobell.ca/sitemap.xml",
        "https://locations.tacobell.co.uk/sitemap.xml",
        # TODO: Different scheme to above, perhaps another spider?
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
            if " in " in item["name"]:
                item["name"], item["branch"] = item["name"].split(" in ", 1)

            if "locations.tacobell.ca" in item["website"]:
                item["extras"]["website:en"] = response.url
                item["extras"]["website:fr"] = response.urljoin(
                    response.xpath('//a[@data-ya-track="language_fr_CA"]/@href').get()
                )
                item["country"] = "CA"
            elif "locations.tacobell.com" in item["website"]:
                if "Cantina" in item["name"]:
                    item.update(self.TACOBELL_CANTINA)
            elif "locations.tacobell.co.uk" in item["website"]:
                item["name"] = "Taco Bell"
            item["image"] = None
            yield item
    drop_attributes = {"image"}
