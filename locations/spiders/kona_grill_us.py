from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KonaGrillUSSpider(Spider):
    name = "kona_grill_us"
    item_attributes = {
        "brand": "Kona Grill",
        "brand_wikidata": "Q6428706",
        "country": "US",
    }
    allowed_domains = ["www.konagrill.com"]
    start_urls = ["https://www.konagrill.com/ajax/getalllocations"]

    def start_requests(self):
        for url in self.start_urls:
            yield FormRequest(url=url, formdata={}, method="POST", callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["data"].values():
            yield FormRequest(url="https://www.konagrill.com/ajax/getlocationdetails", formdata={"id": location["id"]}, method="POST")

    def parse(self, response):
        location = response.json()["data"]
        item = DictParser.parse(location)
        item["street_address"] = item.pop("addr_full", None)
        hours_string = ""
        for hours_type in location["dininghours"].keys():
            # hours_type can be "dining hours", "dining hours ", etc
            if "dining" in hours_type:
                hours_string = " ".join([x["days"] + ": " + x["hours"] for x in location["dininghours"][hours_type]])
        hours_string = hours_string.replace("Brunch (Sat & Sun)", "Sat-Sun")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
