from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.costacoffee_gb import yes_or_no
from locations.spiders.vapestore_gb import clean_address


class ChurchOfEnglandGBSpider(Spider):
    name = "church_of_england_gb"
    item_attributes = {
        "extras": {
            "amenity": "place_of_worship",
            "religion": "christian",
            "denomination": "anglican",
        }
    }
    start_urls = [
        "https://www.achurchnearyou.com/api/internal/venues/venue/?format=json"
    ]

    def parse(self, response, **kwargs):
        for church in response.json()["results"]:
            if not church["is_church"]:
                continue
            item = DictParser.parse(church)
            item["addr_full"] = clean_address(item.get("addr_full"))
            item["image"] = church["photo_image"]
            item["website"] = "https://www.achurchnearyou.com" + church["acny_url"]

            item["extras"] = {"toilets": yes_or_no("toilets" in church["tags"])}

            yield item

        if next_url := response.json()["next"]:
            yield JsonRequest(url=next_url)
