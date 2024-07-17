from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class HairhouseAUSpider(Spider):
    name = "hairhouse_au"
    item_attributes = {"brand": "Hairhouse", "brand_wikidata": "Q118383855"}
    allowed_domains = ["www.hairhouse.com.au"]
    start_urls = [
        "https://www.hairhouse.com.au/api/storeList?latitude=-23.12&longitude=132.13&distance=20000&top=1000&_data=routes%2F(%24lang)%2Fapi%2FstoreList"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json():
            if not location["active"] or not location.get("url_component"):
                # Warehouses do not have a url_component field set.
                continue
            item = DictParser.parse(location)
            item["ref"] = location["internalid"]
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["website"] = "https://www.hairhouse.com.au/stores/" + location["url_component"]
            hours_string = " ".join(
                [day_hours["day"] + ": " + day_hours["hours"] for day_hours in location["operatingHours"]]
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
