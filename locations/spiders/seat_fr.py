import scrapy
import xmltodict

from locations.dict_parser import DictParser


class SeatFrSpider(scrapy.Spider):
    name = "seat_fr"
    item_attributes = {
        "brand": "SEAT",
        "brand_wikidata": "Q188217",
    }
    allowed_domains = ["seat.fr"]
    start_urls = ["https://dealersearch.seat.com/xml?app=seat-fra&brandseat=true&max_dist=3000&city=FR"]

    def parse(self, response):
        data = xmltodict.parse(response.text)
        for store in data.get("result-list", {}).get("partner"):
            item = DictParser.parse(store)
            item["ref"] = store.get("partner_id")
            item["phone"] = store.get("phone1")
            item["lat"] = store.get("mapcoordinate", {}).get("latitude")
            item["lon"] = store.get("mapcoordinate", {}).get("longitude")

            yield item
