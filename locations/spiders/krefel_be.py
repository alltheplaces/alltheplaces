from scrapy import Spider

from locations.dict_parser import DictParser


class KrefelBESpider(Spider):
    name = "krefel_be"
    item_attributes = {"brand": "Krëfel", "brand_wikidata": "Q3200093"}
    start_urls = ["https://api.krefel.be/api/v2/krefel/stores?pageSize=100&lang=fr"]

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["ref"] = location.pop("name")
            location["website"] = f'https://www.krefel.be/fr/magasins/{location["ref"]}'
            location["phone"] = ";".join(
                filter(None, [location["address"].get("phone"), location["address"].get("phone2")])
            ).replace("/", "")
            location["address"]["house_number"] = location["address"].pop("line2", "")
            location["address"]["street"] = location["address"].pop("line1")

            yield DictParser.parse(location)
