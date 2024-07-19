import json
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours


class NatwestGBSpider(Spider):
    name = "natwest_gb"
    item_attributes = {"brand": "NatWest", "brand_wikidata": "Q2740021"}
    total_pois = -1
    seen_refs = set()

    def start_requests(self) -> Iterable[Request]:
        for region in postal_regions("GB"):
            yield JsonRequest(
                url="https://www.natwest.com/content/natwest_com/en_uk/personal/search-results/locator/jcr:content/root/responsivegrid/locator/results.blapi.search.json?{}".format(
                    urlencode(
                        {
                            "search_term": region["postal_region"],
                            "search_limit": "50",
                            "search_radius": "2000",
                            "filter": json.dumps(
                                {"$and": [{"c_brand": {"$eq": "NatWest"}}, {"c_launch": {"$eq": "ACTIVE_BRANCH"}}]}
                            ),
                        }
                    ),
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        resp = response.json()["response"]
        self.total_pois = max([self.total_pois, resp["count"]])
        for location, dist in zip(resp["entities"], resp["distances"]):
            location["location"] = location["displayCoordinate"]
            item = DictParser.parse(location)
            item["ref"] = dist["id"]
            item["branch"] = location["geomodifier"]
            item["website"] = location["c_listing_URL"].replace("/personal", "")
            item["facebook"] = "https://www.facebook.com/{}".format(location["facebookVanityUrl"])
            item["extras"]["ref:facebook"] = location.get("" "facebookPageUrl", "").split("/")[-1]
            item["extras"]["ref:google"] = location["googlePlaceId"]

            if "phone" in item and item["phone"].replace(" ", "").startswith("+443"):
                # not a phone number specific to given branch
                item["phone"] = None

            item["opening_hours"] = OpeningHours()
            for day, rule in location["hours"].items():
                if rule.get("isClosed"):
                    continue
                for time in rule["openIntervals"]:
                    item["opening_hours"].add_range(day, time["start"], time["end"])

            apply_category(Categories.BANK, item)

            yield item
            self.seen_refs.add(item["ref"])

        if len(self.seen_refs) == self.total_pois:
            raise CloseSpider()
