import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.spiders.circle_k import CircleKSpider
from locations.spiders.cvs_us import CvsUSSpider
from locations.spiders.rite_aid_us import RiteAidUSSpider
from locations.spiders.speedway_us import SpeedwayUSSpider
from locations.spiders.target_us import TargetUSSpider
from locations.spiders.walgreens import WalgreensSpider


class BMOHarrisSpider(scrapy.Spider):
    name = "bmo_harris"
    item_attributes = {"brand": "BMO Harris Bank", "brand_wikidata": "Q4835981"}
    allowed_domains = ["branches.bmoharris.com"]
    download_delay = 0.5

    def start_requests(self):
        for lat, lon in point_locations(["us_centroids_100mile_radius.csv", "ca_centroids_100mile_radius.csv"]):
            yield JsonRequest(
                url="https://branchlocator.bmoharris.com/rest/locatorsearch",
                data={
                    "request": {
                        "appkey": "1C92EACC-1A19-11E7-B395-EE7D55A65BB0",
                        "formdata": {
                            "limit": "0",
                            "geolocs": {"geoloc": [{"latitude": lat, "longitude": lon}]},
                            "searchradius": "100",
                        },
                    }
                },
            )

    def parse(self, response, **kwargs):
        res = response.json()
        if res["code"] != 1:
            return

        for shop in res["response"]["collection"]:
            item = DictParser.parse(shop)

            item["ref"] = shop["clientkey"]

            if item["country"] == "US":
                host = "https://branches.bmoharris.com"
            elif item["country"] == "CA":
                host = "https://branches.bmo.com"

                item["brand"] = "BMO"
                item["brand_wikidata"] = "Q806693"

            item["street_address"] = ", ".join(filter(None, [shop.get("address1"), shop.get("address2")]))

            item["website"] = "{}/{}/{}/{}/".format(
                host,
                item["state"].lower(),
                item["city"].lower().replace(" ", "-"),
                item["ref"],
            )

            oh = OpeningHours()
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]:
                oh.add_range(
                    day.title()[:2],
                    shop[day + "open"],
                    shop[day + "close"],
                    time_format="%H%M",
                )

            item["opening_hours"] = oh.as_opening_hours()

            item["extras"] = {}

            if shop["grouptype"] in ["BMOHarrisATM", "BMOATM"]:
                item["extras"]["amenity"] = "atm"

                if item["name"] == "Walgreens":
                    item["located_in"] = WalgreensSpider.WALGREENS["brand"]
                    item["located_in_wikidata"] = WalgreensSpider.WALGREENS["brand_wikidata"]
                elif item["name"] == "CVS":
                    item["located_in"] = CvsUSSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = CvsUSSpider.item_attributes["brand_wikidata"]
                elif item["name"] == "Circle K":
                    item["located_in"] = CircleKSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = CircleKSpider.item_attributes["brand_wikidata"]
                elif item["name"] == "Speedway":
                    item["located_in"] = SpeedwayUSSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = SpeedwayUSSpider.item_attributes["brand_wikidata"]
                elif item["name"] == "Rite Aid":
                    item["located_in"] = RiteAidUSSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = RiteAidUSSpider.item_attributes["brand_wikidata"]
                elif item["name"] == "Target":
                    item["located_in"] = TargetUSSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = TargetUSSpider.item_attributes["brand_wikidata"]
            elif shop["grouptype"] in ["BMOHarrisBranches", "BMOBranches"]:
                item["extras"]["amenity"] = "bank"
            else:
                item["extras"]["type"] = shop["grouptype"]

            yield item
