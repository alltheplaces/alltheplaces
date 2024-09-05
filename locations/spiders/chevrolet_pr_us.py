from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class ChevroletPRUSSpider(Spider):
    name = "chevrolet_pr_us"
    item_attributes = {
        "brand": "Chevrolet",
        "brand_wikidata": "Q29570",
    }
    allowed_domains = ["chevrolet.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        headers = {
            "clientapplicationid": "quantum",
            "locale": "en-US",
        }
        for lat, lon in country_iseadgg_centroids(["PR", "US"], 48):
            yield JsonRequest(
                url=f"https://www.chevrolet.com/bypass/pcf/quantum-dealer-locator/v1/getDealers?desiredCount=50&distance=30&makeCodes=001&latitude={lat}&longitude={lon}&searchType=latLongSearch",
                headers=headers,
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json().get("payload", {}).get("dealers")

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        if len(features) >= 50:
            raise RuntimeError(
                "Locations have probably been truncated due to 50 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 50 results only. Use a smaller search radius."
            )

        for feature in features:
            item = DictParser.parse(feature)
            item["ref"] = feature.get("dealerCode")
            item["name"] = feature.get("dealerName")
            item["website"] = feature.get("dealerUrl")
            item["phone"] = feature.get("generalContact", {}).get("phone1")
            item["state"] = feature.get("address", {}).get("countrySubdivisionCode")
            item["country"] = feature.get("address", {}).get("countryIso")

            item["opening_hours"] = OpeningHours()
            for value in feature.get("generalOpeningHour"):
                for day in value.get("dayOfWeek"):
                    item["opening_hours"].add_range(
                        day=DAYS[day - 1],
                        open_time=value.get("openFrom"),
                        close_time=value.get("openTo"),
                        time_format="%I:%M %p",
                    )

            apply_category(Categories.SHOP_CAR, item)

            yield item
