from chompjs import parse_js_object

from locations.hours import DAYS_DE, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class SteineckeDESpider(JSONBlobSpider):
    name = "steinecke_de"
    item_attributes = {"brand": "Steinecke", "brand_wikidata": "Q57516278"}
    start_urls = ["https://www.steinecke.info/standorte/"]

    def extract_json(self, response):
        js_blob = parse_js_object(response.xpath('//script[@id="gmap-locations-js-extra"]/text()').get())
        return parse_js_object(js_blob["stores"])

    def pre_process_data(self, location):
        location["street_address"] = location.pop("address")

    def post_process_item(self, item, response, location):
        opening_hours = OpeningHours()
        for days, hour_range in location["hours"][0].items():
            opening_hours.add_ranges_from_string(":".join([days, hour_range]), days=DAYS_DE)
        item["opening_hours"] = opening_hours
        yield item
