from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BlakesLotaburgersSpider(Spider):
    name = "blakes_lotaburgers"
    item_attributes = {"brand": "Blakes Lotaburgers", "brand_wikidata": "Q492430"}
    allowed_domains = ["www.lotaburger.com"]
    start_urls = ["https://www.lotaburger.com/wp-json/ip/v1/blakes_location_json/"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            item["ref"] = data["post_id"]
            item["name"] = data["business_name"]
            item["lat"] = data["coords"]["lat"]
            item["lon"] = data["coords"]["long"]
            item["street_address"] = data["business_address"]
            item["city"] = data["business_city"]
            item["state"] = data["business_state"]
            item["postcode"] = data["business_zipcode"]
            item["phone"] = data["business_phone"]
            item["website"] = data["business_url"]
            item["opening_hours"] = OpeningHours()
            raw_string = "".join(
                [
                    opening_data["day"]
                    + " "
                    + opening_data["hours"][0]["from"]
                    + "-"
                    + opening_data["hours"][0]["to"]
                    + "\n"
                    for opening_data in data["store_hours"]
                    if (
                        type(opening_data["hours"][0]["from"]) is not bool
                        and type(opening_data["hours"][0]["to"]) is not bool
                    )
                ]
            )
            item["opening_hours"].add_ranges_from_string(raw_string)
            item["extras"]["breakfast"] = data["breakfast"]
            apply_yes_no(Extras.DRIVE_THROUGH, item, len(data["drive_thru"]) > 0, False)
            yield item
