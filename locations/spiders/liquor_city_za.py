import scrapy

from locations.items import Feature


class LiquorCityZASpider(scrapy.Spider):
    name = "liquor_city_za"
    item_attributes = {
        "brand": "Liquor City",
        "brand_wikidata": "Q116620538",
    }
    start_urls = [
        "https://shop.liquorcity.co.za/api/marketplace/marketplace_get_city_storefronts_v3?domain_name=shop.liquorcity.co.za&post_to_get=1&marketplace_reference_id=01c838877c7b7c7d9f15b8f40d3d2980&marketplace_user_id=742314&latitude=-30.559482&longitude=22.937506&search_text=&filters=undefined&skip=0&limit=5000&self_pickup=1&source=0&dual_user_key=0&language=en"
    ]

    def parse(self, response):
        for location in response.json()["data"]:

            properties = {
                "ref": location["storefront_user_id"],
                "addr_full": location["address"],
                "phone": location["phone"],
                "email": location["email"],
                "lat": location["latitude"],
                "lon": location["longitude"],
                "city": location["display_address"],
            }
            yield Feature(**properties)
