import datetime

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.vapestore_gb import clean_address


class Apotek1NOSpider(Spider):
    name = "apotek_1_no"
    item_attributes = {"brand": "Apotek 1", "brand_wikidata": "Q4581428"}
    start_urls = [
        "https://api.apotek1.no/wcs/resources/store/10151/storelocator/latitude/0/longitude/0?maxItems=1000&radius=2500000&siteLevelStoreSearch=false"
    ]

    def parse(self, response, **kwargs):
        for raw in response.json()["PhysicalStore"]:
            location = {}
            for k, v in raw.items():
                # Some values are padded
                if isinstance(v, str):
                    location[k] = v.strip()
                else:
                    location[k] = v
            # Move Attribute array into the dict for easier access
            for attr in location.pop("Attribute"):
                location[attr["name"]] = attr["value"]

            item = DictParser.parse(location)
            item["name"] = location["Description"][0]["displayStoreName"]
            item["street_address"] = clean_address(location["addressLine"])
            item["state"] = location["stateOrProvinceName"]
            item["ref"] = location["storeName"]
            item["extras"]["fax"] = location["fax1"]
            item["extras"]["start_date"] = datetime.datetime.strptime(location["OpenDate"], "%d.%m.%Y").strftime(
                "%Y-%m-%d"
            )
            item["website"] = "https://www.apotek1.no/vaare-apotek/{}/{}-{}".format(
                location["stateOrProvinceName"].lower().replace(" ", "-"),
                location["RelativeURL"],
                location["storeName"],
            )

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                start = location[f"Open{day}"]
                if start == "STENGT":
                    continue
                item["opening_hours"].add_range(day, start, location[f"Close{day}"])

            yield item
