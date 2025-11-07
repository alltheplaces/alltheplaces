from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours


class CadillacUSSpider(Spider):
    name = "cadillac_us"
    item_attributes = {
        "brand": "Cadillac",
        "brand_wikidata": "Q27436",
    }
    allowed_domains = ["cadillac.com"]

    async def start(self) -> AsyncIterator[Request]:
        headers = {
            "clientapplicationid": "quantum",
            "locale": "en-US",
        }
        for lat, lon in country_iseadgg_centroids(["US"], 158):
            yield Request(
                url=f"https://www.cadillac.com/bypass/pcf/quantum-dealer-locator/v1/getDealers?desiredCount=1000&distance=100&makeCodes=006&latitude={lat}&longitude={lon}&searchType=latLongSearch",
                headers=headers,
            )

    def parse(self, response):
        locations = response.json().get("payload", {}).get("dealers")

        # A maximum of 50 locations are returned at once. The search radius is
        # set to avoid receiving 50 locations in a single response. If 50
        # locations were to be returned, it is a sign that some locations have
        # most likely been truncated.
        if len(locations) >= 50:
            raise RuntimeError(
                "Locations have probably been truncated due to 50 (or more) locations being returned by a single geographic radius search, and the API restricts responses to 50 results only. Use a smaller search radius."
            )

        if len(locations) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for data in locations:
            data.update(data.pop("address"))
            item = DictParser.parse(data)
            item["ref"] = data.get("dealerCode")
            item["name"] = data.get("dealerName")
            item["website"] = data.get("dealerUrl")
            item["phone"] = data.get("generalContact", {}).get("phone1")
            oh = OpeningHours()
            for value in data.get("generalOpeningHour"):
                for day in value.get("dayOfWeek"):
                    oh.add_range(
                        day=DAYS[day - 1],
                        open_time=value.get("openFrom"),
                        close_time=value.get("openTo"),
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_CAR, item)
            departments = [dept.get("name") for dept in data.get("departments", [])]
            apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)
            apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments)
            yield item
