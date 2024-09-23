from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class CanadaPostCASpider(Spider):
    name = "canada_post_ca"
    item_attributes = {"brand": "Canada Post", "brand_wikidata": "Q1032001"}
    allowed_domains = ["pub.geo.canadapost-postescanada.ca"]
    start_urls = [
        "https://pub.geo.canadapost-postescanada.ca/server/rest/services/Hosted/FPO_FLEX_FACILITY_RETAIL_POINT/FeatureServer/0/query?f=json&where=1%3D1&outFields=*&inSR=4326&outSR=4326&resultOffset=0"
    ]

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], meta={"offset": 0})

    def parse(self, response: Response) -> Iterable[Feature | JsonRequest]:
        for feature in response.json()["features"]:
            attributes = feature["attributes"]
            if attributes["grouping"] not in ["Post Office", "Pick and Drop", "Parcel Pickup"]:
                raise RuntimeError("Unknown feature type detected and ignored: {}".format(attributes["grouping"]))
                continue

            item = DictParser.parse(attributes)
            item["ref"] = attributes["site"]
            item.pop("name", None)
            item["branch"] = attributes["displaynameen"]
            item["lat"] = feature["geometry"]["y"]
            item["lon"] = feature["geometry"]["x"]
            item["street_address"] = attributes["structureaddress"]
            item["opening_hours"] = self.parse_opening_hours(feature)

            if attributes["grouping"] == "Post Office":
                apply_category(Categories.POST_OFFICE, item)
            elif attributes["grouping"] == "Pick and Drop":
                apply_category(Categories.POST_PARTNER, item)
                item["brand"] = None
                item["brand_wikidata"] = None
                item["operator"] = attributes["sitebusinessname"]
                item["extras"]["post_office:brand"] = self.item_attributes["brand"]
                item["extras"]["post_office:brand:wikidata"] = self.item_attributes["brand_wikidata"]
                item["extras"]["post_office:letter_from"] = "Canada Post"
                item["extras"]["post_office:parcel_from"] = "Canada Post"
                item["extras"]["post_office:parcel_to"] = "Canada Post"
                item["extras"]["post_office:stamps"] = "Canada Post"
                item["extras"]["post_office:packaging"] = "Canada Post"
            elif attributes["grouping"] == "Parcel Pickup":
                apply_category(Categories.POST_PARTNER, item)
                item["brand"] = None
                item["brand_wikidata"] = None
                item["operator"] = attributes["sitebusinessname"]
                item["extras"]["post_office:brand"] = self.item_attributes["brand"]
                item["extras"]["post_office:brand:wikidata"] = self.item_attributes["brand_wikidata"]
                item["extras"]["post_office:parcel_to"] = "Canada Post"

            yield item

        if response.json()["exceededTransferLimit"]:
            # More features exist but have been truncated.
            # Request the next page of features.
            offset = response.meta["offset"] + 2000
            yield JsonRequest(
                url=self.start_urls[0].replace("&resultOffset=0", f"&resultOffset={offset}"), meta={"offset": offset}
            )

    def parse_opening_hours(self, feature: dict) -> OpeningHours():
        hours_keys_list = [
            ("Mo", "openmonam", "closemonam", "openmonpm", "closemonpm"),
            ("Tu", "opentueam", "closetueam", "opentuepm", "closetuepm"),
            ("We", "openwedam", "closewedam", "openwedpm", "closewedpm"),
            ("Th", "openthuam", "closethuam", "openthupm", "closethupm"),
            ("Fr", "openfriam", "closefriam", "openfripm", "closefripm"),
            ("Sa", "opensatam", "closesatam", "opensatpm", "closesatpm"),
            ("Su", "opensunam", "closesunam", "opensunpm", "closesunpm"),
        ]
        oh = OpeningHours()
        for hours_keys in hours_keys_list:
            day_abbrev = feature.get(hours_keys[0])
            am_open = feature.get(hours_keys[1])
            am_close = feature.get(hours_keys[2])
            pm_open = feature.get(hours_keys[3])
            pm_close = feature.get(hours_keys[4])
            if am_open and not am_close and not pm_open and pm_close:
                oh.add_range(day_abbrev, am_open, pm_close, "%H:%M:%S")
            elif am_open and am_close and pm_open and pm_close:
                oh.add_range(day_abbrev, am_open, am_close, "%H:%M:%S")
                oh.add_range(day_abbrev, pm_open, pm_close, "%H:%M:%S")
        return oh
