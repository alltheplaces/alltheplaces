import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HaypostAmSpider(Spider):
    name = "haypost_am"
    item_attributes = {"brand": "ՀայՓոստ", "brand_wikidata": "Q3128876"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://api.haypost.am/page/10?lng=am")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The "Our network" page config holds the region and city id -> name lookups used by the offices feed.
        regions = response.json()["module"]["region"]
        yield JsonRequest(
            url="https://api.haypost.am/network?limit=1000&lng=am",  # the API defaults to 500 rows
            callback=self.parse_offices,
            cb_kwargs={
                "regions": {region["id"]: region["name"] for region in regions},
                "cities": {city["id"]: (city["name"], region["id"]) for region in regions for city in region["cities"]},
            },
        )

    def parse_offices(
        self, response: Response, regions: dict[int, str], cities: dict[int, tuple[str, int]], **kwargs: Any
    ) -> Any:
        for location in response.json():
            if location["address"].startswith("Postmobil"):
                continue  # mobile post van, no fixed location
            item = DictParser.parse(location)
            # "postal_code" is the office's own index (Փոստային դասիչ), not reliably the postcode of its address.
            item.pop("postcode", None)
            item["state"] = regions.get(location["region"])
            # The city lookup has missing ids, cities filed under another region and disambiguated or abbreviated
            # names ("Ապարան(Շենավան)", "Ն.գետաշեն", "գ․ Արաքս"), so only clean, consistent names are kept.
            city_name, city_region = cities.get(location["city"], ("", None))
            item["city"] = (
                city_name if city_region == location["region"] and not re.search(r"[(.․]", city_name) else None
            )
            # A couple of offices list weekdays here that contradict the Mon-Fri hours the site displays.
            if not location["working_days"]:
                item["opening_hours"] = self.parse_opening_hours(location)
            apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for key, days in (("work_days", DAYS[:5]), ("saturday", ["Sa"]), ("sunday", ["Su"])):
            if not location[key]:
                oh.set_closed(days)  # the site shows these days as "Ոչ աշխատանքային" (non-working)
                continue
            try:
                start, close = self.parse_range(location[key])
                # The lunch break and the time staff are out delivering ("outside") both close the office.
                gaps = [location[f"{key}_{gap}"] for gap in ("break_time", "outside") if location[f"{key}_{gap}"]]
                for gap_start, gap_end in sorted(map(self.parse_range, gaps)):
                    if start < gap_start and start < close:
                        oh.add_days_range(days, start, min(gap_start, close))
                    start = max(start, gap_end)
                if start < close:
                    oh.add_days_range(days, start, close)
            except ValueError:
                self.crawler.stats.inc_value("atp/{}/hours/failed".format(self.name))
        return oh

    @staticmethod
    def parse_range(value: str) -> tuple[str, str]:
        start, end = (time.strip().zfill(5) for time in value.split("-"))
        return start, end
