from math import ceil
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_UA, OpeningHours
from locations.items import Feature

MEEST = {"brand": "Meest", "brand_wikidata": "Q25432124"}


class MeestUASpider(Spider):
    name = "meest_ua"
    # Without a sort order the pages overlap and some branches are never returned
    api = "https://geo.meest.com/api/v1/map/branch/all?limit=200&sort=number&order=asc&page={}"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(self.api.format(1))

    def parse(self, response: Response, page: int = 1) -> Any:
        result = response.json()["result"]
        if page == 1:
            for next_page in range(2, ceil(result["count"] / 200) + 1):
                yield JsonRequest(self.api.format(next_page), cb_kwargs={"page": next_page})

        for branch in result["data"]:
            item = Feature()
            item["ref"] = branch["uuid"]
            item["lat"] = branch["latitude"]
            item["lon"] = branch["longitude"]
            item["street"] = "{} {}".format(branch["street_type"], branch["street_name_ua"])
            item["housenumber"] = branch["house"]
            item["city"] = branch["city_name_ua"]
            item["postcode"] = branch["index"]
            item["phone"] = branch["phone"]

            if branch["branch_type"] == "АПТ":
                item.update(MEEST)
                apply_category(Categories.PARCEL_LOCKER, item)
            elif branch["branch_type"] in ("ОВ", "ППВ", "МППВ"):
                item["operator"] = MEEST["brand"]
                item["operator_wikidata"] = MEEST["brand_wikidata"]
                apply_category(Categories.POST_OFFICE, item)
            else:
                # Mini branches are counters inside partner shops, petrol stations and so on
                apply_category(Categories.GENERIC_POI, item)
                apply_category({"post_office": "post_partner"}, item)
                item.set_tag("post_office:brand", MEEST["brand"])
                item.set_tag("post_office:brand:wikidata", MEEST["brand_wikidata"])

            item["opening_hours"] = OpeningHours()
            for day in branch["branch_work_time"]:
                if not day["time_from"]:
                    item["opening_hours"].set_closed(DAYS_UA[day["day"]])
                elif day["lunch_break_from"]:
                    item["opening_hours"].add_range(DAYS_UA[day["day"]], day["time_from"], day["lunch_break_from"])
                    item["opening_hours"].add_range(DAYS_UA[day["day"]], day["lunch_break_to"], day["time_to"])
                else:
                    item["opening_hours"].add_range(DAYS_UA[day["day"]], day["time_from"], day["time_to"])

            yield item
