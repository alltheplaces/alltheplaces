import scrapy

from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class AllsupsSpider(scrapy.Spider):
    name = "allsups"
    item_attributes = {"brand": "Allsup's", "brand_wikidata": "Q4733292"}
    allowed_domains = ["allsups.com"]
    start_urls = [
        "https://allsups.com/wp-json/acf/v3/business_locations?_embed&per_page=1000",
    ]

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "ref": store["acf"]["internal_store_code"],
                "name": store["acf"]["business_name"],
                "street_address": clean_address([store["acf"]["address_line_1"], store["acf"]["address_line_2"]]),
                "city": store["acf"]["city"],
                "state": store["acf"]["state"],
                "postcode": store["acf"]["postal_code"],
                "country": store["acf"]["country"],
                "lat": store["acf"]["latitude"],
                "lon": store["acf"]["longitude"],
                "phone": store["acf"]["primary_phone"],
            }

            yield Feature(**properties)
