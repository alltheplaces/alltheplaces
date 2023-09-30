import reverse_geocoder
from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class HouseAUSpider(Spider):
    name = "house_au"
    item_attributes = {"brand": "House", "brand_wikidata": "Q117921987"}
    allowed_domains = ["www.house.com.au"]
    start_urls = ["https://www.house.com.au/api/get-stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, method="POST")

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)

            # Some stores have wildly incorrect coordinates for
            # locations as far away as France. Only add geometry
            # where coordinates existing within Australia.
            if result := reverse_geocoder.get((location["latitude"], location["longitude"]), mode=1, verbose=False):
                if result["cc"] == "AU":
                    item["geometry"] = location["location"]

            item["street_address"] = ", ".join(filter(None, [location["address1"], location["address2"]]))
            item["website"] = "https://www.house.com.au/stores/" + location["slug"]
            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["storeHours"].items():
                if hours["open"] == "-" or hours["close"] == "-":
                    continue
                item["opening_hours"].add_range(
                    day_name.title(),
                    hours["open"].replace(".", ":"),
                    hours["close"].replace(".", ":").replace(":-", ":"),
                )
            yield item
