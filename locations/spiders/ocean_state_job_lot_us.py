import scrapy

from locations.dict_parser import DictParser


class OceanStateJobLotUSSpider(scrapy.Spider):
    name = "ocean_state_job_lot_us"
    item_attributes = {"brand": "Ocean State Job Lot", "brand_wikidata": "Q7076076"}
    start_urls = ["https://www.oceanstatejoblot.com/stat/api/locations/search?limit=1000000"]

    def parse(self, response):
        for store in response.json()["locations"]:
            item = DictParser.parse(store)
            item["city"] = store["businessAddress"]["addressLocality"]
            item["state"] = store["businessAddress"]["addressRegion"]
            item["postcode"] = store["businessAddress"]["postalCode"]
            item["street_address"] = store["businessAddress"]["streetAddress"]
            item["website"] = "https://www.oceanstatejoblot.com/" + store["link"]
            item["geometry"] = {"type": "Point", "coordinates": [store["coordinates"][0], store["coordinates"][1]]}
            yield item
