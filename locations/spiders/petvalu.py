import scrapy

from locations.dict_parser import DictParser


class PetValuSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "petvalu"
    item_attributes = {"brand": "Pet Valu", "brand_wikidata": "Q58009635"}
    allowed_domains = ["store.petvalu.ca"]
    start_urls = (
        "https://store.petvalu.ca/stat/api/locations/search?lng=-73.9818&lat=40.7263&kilometers=3000&limit=200&fields=servicetags_bosleys,servicetags_paulmacs,servicetags_tisol_2,servicetags_total_pet_2,servicetags_petvalu_2,displayname_location_name",
    )

    def parse(self, response):
        data = response.json()
        for store in data["locations"]:
            store.update(store.pop("businessAddress"))
            item = DictParser.parse(store)
            item["ref"] = store["clientLocationId"]
            item["lon"], item["lat"] = store["coordinates"]
            item["phone"] = store["primaryPhone"]
            item["website"] = "https://store.petvalu.ca/store/" + store["link"]
            yield item
