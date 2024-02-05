import scrapy

from locations.dict_parser import DictParser


class GrycanPLSpider(scrapy.Spider):
    name = "grycan_pl"
    item_attributes = {"brand": "Grycan", "brand_wikidata": "Q97372889"}

    def start_requests(self):
        yield scrapy.FormRequest(
            url="https://grycan.pl/wp-json/wpgmza/v1/marker-listing/",
            formdata={"phpClass": "WPGMZA\\MarkerListing\\BasicList", "mapid": "1", "start": "0", "length": "1000"},
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for store in response.json().get("meta"):
            item = DictParser.parse(store)
            item["image"] = store.get("pic")
            yield item
