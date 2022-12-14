import scrapy
import xmltodict

from locations.dict_parser import DictParser


class BeerBmwFrSpider(scrapy.Spider):
    name = "bmw_fr"
    item_attributes = {
        "brand": "BMW",
        "brand_wikidata": "Q26678",
    }
    allowed_domains = ["bmw.fr"]
    start_urls = [
        "https://www.bmw.fr/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/FR/pois?brand=BMW_BMWI_BMWM&cached=off&category=BM&country=FR&language=fr&lat=0&lng=0&maxResults=700&showAll=true&unit=km"
    ]

    def parse(self, response):
        json_data = xmltodict.parse(response.text)
        results = json_data["result"]["data"]["pois"]["poi"]
        for data in results:
            item = DictParser.parse(data)
            item["ref"] = data.get("key")
            item["phone"] = data.get("attributes", {}).get("phone")
            item["email"] = data.get("attributes", {}).get("mail")
            item["website"] = data.get("attributes", {}).get("homepage")

            yield item
