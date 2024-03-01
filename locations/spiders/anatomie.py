import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AnatomieSpider(scrapy.Spider):
    name = "anatomie"
    item_attributes = {"brand": "Anatomie", "brand_wikidata": "Q115608133"}
    allowed_domains = ["stores.boldapps.net"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://stores.boldapps.net/front-end/get_surrounding_stores.php?shop=anatomie-store.myshopify.com&latitude=38.331258&longitude=-121.54841799999997&max_distance=100000&limit=10000&calc_distance=1",
    )

    def parse(self, response):
        json_data = response.json()
        for item in json_data["stores"]:
            properties = {
                "street_address": merge_address_lines([item["address"], item["address2"]]),
                "name": item["name"],
                "city": item["city"],
                "state": item["prov_state"],
                "country": item["country"],
                "postcode": item["postal_zip"],
                "ref": item["store_id"],
                "phone": item["phone"],
                "website": item["website"],
                "lat": float(item["lat"]),
                "lon": float(item["lng"]),
                "extras": {"check_date": item["updated_at"]},
            }
            yield Feature(**properties)
