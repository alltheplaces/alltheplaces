
import scrapy

from locations.dict_parser import DictParser


class PetValuSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "petvalu"
    item_attributes = {"brand": "Pet Valu", "brand_wikidata": "Q58009635"}
    allowed_domains = ["store.petvalu.ca"]
    start_urls = (
        "https://store.petvalu.ca/modules/multilocation/?near_location=toronto&threshold=40000000000000&geocoder_components=country:CA&distance_unit=km&limit=20000000000&services__in=&language_code=en-us&published=1&within_business=true",
    )

    def parse(self, response):
        data = response.json()
        for i in data["objects"]:
            i["street_address"] = i.pop("street")
            item = DictParser.parse(i)
            item["addr_full"] = i["formatted_address"]
            item["website"] = i["location_url"]
            yield item
