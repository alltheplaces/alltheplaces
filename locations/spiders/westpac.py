from typing import Any

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WestpacSpider(Spider):
    name = "westpac"
    BRAND_MAPPING = {
        "bom": ("BOM", "Q4856151"),
        "bsa": ("BankSA", "Q4856181"),
        "fid": ("Precinct", ""),
        "stg": ("St.George", "Q1606050"),
        "wbc": ("Westpac", "Q2031726"),
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DOWNLOAD_TIMEOUT": 300,
        "DOWNLOAD_DELAY": 5,
        "RETRY_TIMES": 10,
    }
    api = "https://digital-api.westpac.com.au/cap/chnl/lcteus/svc/v1/prcng-svc-dtl?upperLatitude=90&lowerLatitude=-90&eastLongitude=180&westLongitude=-180"
    # Start interaction with API using lower zoom_level, directly using max_zoom_level might result in non-responsive API behavior.
    start_urls = [f"{api}&zoomLevel=11&searchType=atm"]
    max_zoom_level = "19"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # After making request with lower zoom_level, now attempt with max_zoom_level to get max available count.
        for location_type in ["branch", "atm"]:
            yield JsonRequest(
                url=f"{self.api}&zoomLevel={self.max_zoom_level}&searchType={location_type}",
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        if not response.json().get("map") or "locations" not in response.json()["map"][-1]:
            # sometimes API responds only after multiple tries
            yield get_retry_request(response.request, spider=self, reason="missing desired data", max_retry_times=10)
        else:  # successful request
            for location in response.json()["map"][-1][-1]:
                item = DictParser.parse(location)
                item["ref"] = location["markerPointId"]
                if location["brandCode"] == "ats":  # ATMX locations covered by Armaguard AU Spider
                    continue
                if brand_details := self.BRAND_MAPPING.get(location["brandCode"]):
                    item["brand"], item["brand_wikidata"] = brand_details
                else:
                    self.crawler.stats.inc_value(f'atp/unknown_brand/{location["brandName"]}')

                if location_type := location.get("serviceProviderTypeName"):
                    if location_type.upper() == "ATM":
                        apply_category(Categories.ATM, item)
                    elif location_type.upper() == "BRANCH":
                        apply_category(Categories.BANK, item)
                    elif location_type.upper() == "CDM":  # Cash Deposit Machine
                        apply_category(Categories.ATM, item)
                        apply_yes_no(Extras.CASH_IN, item, True)
                        apply_yes_no(Extras.CASH_OUT, item, False)
                    elif location_type.upper() == "CEM":  # Cash Exchange Machine
                        apply_category(Categories.ATM, item)
                        apply_yes_no(Extras.CASH_IN, item, True)
                        apply_yes_no(Extras.CASH_OUT, item, True)
                    else:
                        self.crawler.stats.inc_value(f"atp/unmapped_category/{location_type}")

                    if location_type.upper() == "BRANCH":
                        item["website"] = (
                            f'https://www.westpac.com.au/locateus/branch/{item["state"]}/{item["city"]}/{item["name"]}'.replace(
                                " ", ""
                            )
                        )
                    elif location["brandCode"] == "wbc":
                        item["website"] = (
                            f'https://www.westpac.com.au/locateus/{location_type.upper()}/{location["locationId"]}'
                        )
                    else:
                        item["website"] = (
                            f'https://www.westpac.com.au/locateus/{location_type.upper()}/{location["brandCode"]}/{location["locationId"]}'
                        )

                if services := location.get("services"):
                    item["opening_hours"] = OpeningHours()
                    for day in DAYS_FULL:
                        open_time, close_time = services[0].get(f"{day.lower()}OpenTime"), services[0].get(
                            f"{day.lower()}CloseTime"
                        )
                        if open_time and close_time:
                            item["opening_hours"].add_range(day, open_time, close_time, time_format="%I:%M%p")

                yield item
