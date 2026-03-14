from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GiuntiAlPuntoITSpider(Spider):
    name = "giunti_al_punto_it"
    item_attributes = {"brand": "Giunti al Punto", "brand_wikidata": "Q76505309"}
    start_urls = ["https://stores-giunti.retailtune.com/endpoint/sl/list.json.php"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Authorization": "Basic Z2l1bnRpX2VuZHBvaW50X3VzZXI6eTBKeEZ5Z0ZwMFZkb0ExY3R2b2c="}
    }

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location["store"])
            item["street_address"] = location["store"]["address_1"]
            item["extras"]["check_date"] = location["last-modified"]

            item["opening_hours"] = OpeningHours()
            for day, rule in location["store"]["hours"].items():
                if rule["close"]:
                    item["opening_hours"].add_range(day, "closed", "closed")
                else:
                    item["opening_hours"].add_range(day, rule["morningOpen"], rule["morningClose"])
                    item["opening_hours"].add_range(day, rule["eveningOpen"], rule["eveningClose"])

            yield item
