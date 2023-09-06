import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT

BRANDS = {"MS": "Motel 6", "SS": "Studio 6", "HS": "Hotel 6"}


class Motel6Spider(scrapy.Spider):
    name = "motel6"
    item_attributes = {"brand": "Motel 6", "brand_wikidata": "Q2188884"}
    start_urls = ["https://www.motel6.com/content/g6-cache/property-summary.1.json"]
    download_delay = 0.5
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse(self, response):
        for hotel_id in response.json().keys():
            try:
                url = "https://www.motel6.com/bin/g6/propertydata.{}.json".format(int(hotel_id))
                yield scrapy.Request(url, callback=self.parse_hotel)
            except ValueError:
                continue

    def parse_hotel(self, response):
        data = response.json()
        address = data.pop("address", {})
        item = DictParser.parse(data)
        item["ref"] = data["property_id"]
        item["street_address"] = address.get("address_line_0")
        item["website"] = "https://www.motel6.com/en/home/motels.{}.{}.{}.html".format(
            data["state"].lower(),
            data["city"].lower().replace(" ", "-"),
            data["property_id"],
        )
        item["image"] = "https://www.motel6.com/bin/g6/image.g6PropertyDetailSlider.jpg" + data["lead_image_path"]
        item["brand"] = BRANDS[data["brand_id"]]
        yield item
