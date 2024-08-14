import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class ModPizzaSpider(scrapy.spiders.SitemapSpider):
    name = "mod_pizza"
    item_attributes = {
        "brand": "MOD Pizza",
        "brand_wikidata": "Q19903469",
        "country": "US",
    }

    allowed_domains = ["locations.modpizza.com"]
    sitemap_urls = [
        "https://locations.modpizza.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"https://locations\.modpizza\.com/.+\/.+\/.+\/.+", "parse"),
    ]

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "FastFoodRestaurant")

        # The address isn't in the microdata.
        item["street_address"] = response.css(".Address-field.Address-line1::text").get()
        item["city"] = response.css(".Address-city::text").get()
        item["state"] = response.css(".Address-field.Address-region::text").get()
        item["postcode"] = response.css(".Address-field.Address-postalCode::text").get()

        yield item
