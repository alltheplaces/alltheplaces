import re

from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.harcourts import HARCOURTS_SHARED_ATTRIBUTES


class HarcourtsZASpider(JSONBlobSpider):
    name = "harcourts_za"
    start_urls = ["https://www.harcourts.co.za/branches/"]

    def extract_json(self, response):
        locations_js = (
            response.xpath('//script[contains(text(), "var branches_points = ")]/text()')
            .get()
            .split("var branches_points = ", 1)[1]
        )
        return parse_js_object(locations_js)

    def post_process_item(self, item, response, location):
        if "Harcourts" in item["name"]:
            item["branch"] = item.pop("name").replace("Harcourts ", "")
            item.update(HARCOURTS_SHARED_ATTRIBUTES)
            item["name"] = item["brand"]
        elif "rentalsdotcom" in item["name"].lower():
            re.sub(r"rentalsdotcom\s", "", item["name"], flags=re.IGNORECASE)
            item["branch"] = item.pop("name").replace("Rentalsdotcom ", "")
            item["brand"] = "RentalsDotCom"
            item["brand_wikidata"] = HARCOURTS_SHARED_ATTRIBUTES["brand_wikidata"]
            item["name"] = item["brand"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{item['name']}")
        item["phone"] = location.get("get_dialable_telephone_number") + "; " + location.get("get_dialable_cell_number")
        item["lat"] = location.get("map_x_position")
        item["lon"] = location.get("map_y_position")
        item["website"] = "https://www.harcourts.co.za" + location["url"]
        try:
            int(item["addr_full"].split(",")[-1])
            item["postcode"] = item["addr_full"].split(",")[-1]
            item["city"] = item["addr_full"].split(",")[-2]
        except ValueError:
            pass
        yield item
