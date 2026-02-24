from json import dumps
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours


class NatwestGBSpider(Spider):
    name = "natwest_gb"
    item_attributes = {"brand": "NatWest", "brand_wikidata": "Q2740021"}
    total_pois = -1
    seen_refs = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for region in postal_regions("GB"):
            yield JsonRequest(
                url="https://www.natwest.com/content/natwest_com/en_uk/personal/search-results/locator/jcr:content/root/responsivegrid/locator/results.blapi.search.json?{}".format(
                    urlencode(
                        {
                            "search_term": region["postal_region"],
                            "search_limit": "50",
                            "search_radius": "2000",
                            "filter": dumps(
                                {
                                    "$and": [
                                        {"c_brand": {"$eq": "NatWest"}},
                                        {
                                            "$or": [
                                                {"meta.entityType": {"$eq": "atm"}},
                                                {"meta.entityType": {"$eq": "location"}},
                                                {"meta.entityType": {"$eq": "ce_mobileBranches"}},
                                            ]
                                        },
                                    ]
                                }
                            ),
                        }
                    ),
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        resp = response.json()["response"]
        self.total_pois = max([self.total_pois, resp["count"]])
        for location in resp["entities"]:
            location.update(location.pop("meta", {}))
            if coordinates := location.get("displayCoordinate"):
                location["location"] = coordinates
            item = DictParser.parse(location)
            item["website"] = (
                location["c_listing_URL"].replace("/personal", "").replace(" ", "-")
                if location.get("c_listing_URL")
                else None
            )

            if location.get("entityType") == "location":
                if item["name"].endswith("Banking Hub"):
                    item["branch"] = item.pop("name").removesuffix("Banking Hub")
                    item["name"] = "Banking Hub"
                    apply_category(Categories.BANK, item)
                else:
                    item["branch"] = item.pop("name").removeprefix("NatWest")
                    item["name"] = "NatWest"
                    apply_category(Categories.BANK, item)

                apply_yes_no(
                    Extras.ATM, item, location.get("c_externalATM") == "1" or location.get("c_internalATM") == "1"
                )

                if "facebookVanityUrl" in location:
                    item["facebook"] = "https://www.facebook.com/{}".format(location["facebookVanityUrl"])

                item["extras"]["ref:facebook"] = location.get("facebookPageUrl", "").split("/")[-1]
                item["extras"]["ref:google:place_id"] = location.get("googlePlaceId")

                item["phone"] = None
            elif location.get("entityType") == "ce_mobileBranches":
                item["branch"] = item.pop("name").removesuffix(" Mobile Branch")
                item["name"] = "NatWest Mobile Branch"
                apply_category(Categories.BANK, item)
            elif location.get("entityType") == "atm":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, location.get("c_cashdepositMachine") == "1")

            if hours := location.get("hours"):
                item["opening_hours"] = OpeningHours()
                for day, rule in hours.items():
                    if rule.get("isClosed"):
                        continue
                    for time in rule["openIntervals"]:
                        item["opening_hours"].add_range(day, time["start"], time["end"])

            yield item
            self.seen_refs.add(item["ref"])

        if len(self.seen_refs) == self.total_pois:
            raise CloseSpider()
