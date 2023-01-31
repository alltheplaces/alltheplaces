from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RexelSpider(Spider):
    base_url = ""
    search_lat = ""
    search_lon = ""

    # This seems to return all stores regardless of lat-long; as long as it's in the right country/area?
    start_urls = [
        f"https://{self.base_url}/store-finder/findNearbyStores?latitude={self.search_lat}&longitude={self.search_lon}"
    ]

    def parse(self, response):
        for store in response.json()["results"]:
            store["address"]["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        store["address"].pop("line1"),
                        store["address"].pop("line2"),
                        store["address"].pop("line3"),
                    ],
                )
            )
            store["ref"] = store.pop("name")
            item = DictParser.parse(store)
            item["phone"] = store["address"]["phone"]
            # e.g. https://www.denmans.co.uk/den/Bradley-Stoke-Bristol/store/1AR
            item[
                "website"
            ] = f'https://{self.base_url}/{store["address"]["town"].replace(" ", "-")}/store/{store["ref"]}'
            item["opening_hours"] = self.decode_hours(store)
            # We could also fall back to cartIcon here...
            storeImages = filter(lambda x: (x["format"] == "store" and x["url"]), store["storeImages"])
            if storeImages:
                item["image"] = next(storeImages)["url"]
            yield from self.parse_item(item, feature) or []

    @staticmethod
    def decode_hours(store):
        oh = OpeningHours()
        for r in filter(lambda x: (not x["closed"]), store["openingHours"]["rexelWeekDayOpeningList"]):
            oh.add_range(
                r["weekDay"],
                r["openingTime"]["formattedHour"],
                r["closingTime"]["formattedHour"],
                time_format="%I:%M %p",
            )
        return oh
