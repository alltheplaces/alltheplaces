import scrapy

from locations.items import Feature


class SteakNShakeSpider(scrapy.Spider):
    name = "steak_n_shake"
    item_attributes = {"brand": "Steak 'n Shake", "brand_wikidata": "Q7605233"}
    allowed_domains = ["www.steaknshake.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://www.steaknshake.com/wp-admin/admin-ajax.php",
            formdata={"action": "get_location_data_from_plugin"},
        )

    def parse(self, response):
        for store_data in response.json():
            properties = {
                "ref": store_data["brandChainId"],
                "name": store_data["name"],
                "street_address": store_data["address"]["address1"],
                "city": store_data["address"]["city"],
                "state": store_data["address"]["region"],
                "postcode": store_data["address"]["zip"],
                "country": store_data["address"]["country"],
                "phone": store_data["phone1"],
                "lat": store_data["address"]["loc"][1],
                "lon": store_data["address"]["loc"][0],
                "website": f"https://www.steaknshake.com/locations/{store_data['slug']}/",
            }
            yield Feature(**properties)
