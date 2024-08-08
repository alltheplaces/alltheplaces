from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RexelSpider(Spider):
    base_url = ""
    search_lat = ""
    search_lon = ""

    def start_requests(self):
        # This seems to return all stores regardless of lat-long; as long as it's in the right country/area?
        yield JsonRequest(
            url=f"https://{self.base_url}/store-finder/findNearbyStores?latitude={self.search_lat}&longitude={self.search_lon}"
        )

    def parse(self, response):
        for feature in response.json()["results"]:
            feature["address"]["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        feature["address"].pop("line1"),
                        feature["address"].pop("line2"),
                        feature["address"].pop("line3"),
                    ],
                )
            )
            feature["ref"] = feature.pop("name")
            item = DictParser.parse(feature)
            if not feature["address"]["phone"].replace(" ", "").startswith("+443"):
                item["phone"] = feature["address"]["phone"]
            # e.g. https://www.denmans.co.uk/den/Bradley-Stoke-Bristol/store/1AR
            item["website"] = (
                f'https://{self.base_url}/{feature["address"]["town"].replace(" ", "-")}/store/{feature["ref"]}'
            )
            item["opening_hours"] = self.decode_hours(feature)
            # We could also fall back to cartIcon here...
            if feature["storeImages"]:
                store_images = filter(lambda x: (x["format"] == "store" and x["url"]), feature["storeImages"])
                if store_images:
                    item["image"] = next(store_images)["url"]
            yield from self.parse_item(item, feature) or []

    def parse_item(self, item, feature, **kwargs):
        yield item

    @staticmethod
    def decode_hours(feature):
        oh = OpeningHours()
        if feature["openingHours"] and feature["openingHours"]["rexelWeekDayOpeningList"]:
            for r in filter(lambda x: (not x["closed"]), feature["openingHours"]["rexelWeekDayOpeningList"]):
                oh.add_range(
                    r["weekDay"],
                    r["openingTime"]["formattedHour"],
                    r["closingTime"]["formattedHour"],
                    time_format="%I:%M %p",
                )
                return oh
