from itertools import islice

from chompjs import parse_js_objects

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class SteineckeDESpider(JSONBlobSpider):
    name = "steinecke_de"
    item_attributes = {"brand": "Steinecke", "brand_wikidata": "Q57516278"}
    start_urls = ["https://www.steinecke.info/standorte/"]

    def extract_json(self, response):
        js_objects = parse_js_objects(response.xpath('//script/text()[contains(., "locations_data")]').get())
        return next(islice(js_objects, 1, None))

    def post_process_item(self, item, response, location):
        item["ref"] = item["website"] = location["permalink"]
        opening_hours = OpeningHours()
        for day, hour_range in location["opening_hours"].items():
            if hour_range:
                start_time, end_time = hour_range.split("-")
                opening_hours.add_range(day, start_time, end_time)
        item["opening_hours"] = opening_hours
        item["branch"] = item.pop("name")
        yield item
