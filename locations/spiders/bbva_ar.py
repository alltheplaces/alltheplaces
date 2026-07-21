from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class BbvaARSpider(Spider):
    name = "bbva_ar"
    item_attributes = {"brand": "BBVA Argentina", "brand_wikidata": "Q2876788"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}  # the API returns HTTP 403 to non-browser user agents
    requires_proxy = "AR"  # Akamai also blocks data-centre IPs (CI fetch gets HTTP 403); needs an AR proxy

    async def start(self) -> AsyncIterator[Any]:
        # Country-wide radius from Buenos Aires returns all branches at once; branchType filters to public
        # retail branches (COMPANIES/CORPORATE are administrative units co-located at head office). The API
        # exposes no ATMs (branchType=ATM and /pois/v0/atms are both empty).
        yield JsonRequest(
            url="https://servicios.bbva.com.ar/openmarket/servicios/pois/v0/branches"
            "?latitude=-34.6037345&longitude=-58.3837591&radius=5000000&branchType=INDIVIDUALS,INTEGRAL"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.json()["data"]:
            item = DictParser.parse(branch)  # maps id (-> ref), city, zipCode (-> postcode)
            item.pop("state", None)  # address.state duplicates city (locality name, not a province)
            item.pop("phone", None)  # telephone has no area code (6-8 local digits), not a dialable number
            item["branch"] = branch["description"]
            item["street_address"] = branch["address"]["addressName"]
            item["lat"] = branch["address"]["geolocation"]["latitude"]
            item["lon"] = branch["address"]["geolocation"]["longitude"]
            item["opening_hours"] = self.parse_opening_hours(branch["openingHours"])
            apply_category(Categories.BANK, item)
            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours | None:
        try:
            oh = OpeningHours()
            for rule in rules:
                oh.add_range(rule["dayOfWeek"], rule["from"], rule["to"], time_format="%H:%M:%S")
            return oh
        except (KeyError, ValueError):
            return None
