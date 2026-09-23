import html
import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# The locations page is a Livewire component whose wire:snapshot attribute holds
# every site, nested by state, with address and coordinates. Opening hours are
# only on the per site pages, in a JSON-LD block that is not valid JSON — the
# days are written as {"dayOfWeek": ["Monday": "08:00-19:00", ...]} — so they
# are read with a regular expression rather than a JSON parse.


class ZipsCarWashUSSpider(Spider):
    name = "zips_car_wash_us"
    item_attributes = {"brand": "ZIPS Car Wash", "brand_wikidata": "Q124649852"}
    allowed_domains = ["zipscarwash.com"]
    start_urls = ["https://zipscarwash.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        if not (snapshot := re.search(r'wire:snapshot="(.*?)"\s', response.text, re.S)):
            self.logger.error("No Livewire snapshot on the locations page")
            return

        for location in self.iter_sites(json.loads(html.unescape(snapshot.group(1)))["data"]["locations"]):
            item = Feature()
            item["ref"] = location["site_id"]
            item["branch"] = (location.get("name") or "").removeprefix("ZIPS - ")
            item["street_address"] = location.get("address")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zipcode")
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["website"] = response.urljoin(
                f"/locations/{location['state'].lower()}/{location['city_slug']}/{location['address_slug']}"
            )

            apply_category(Categories.CAR_WASH, item)

            yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    @staticmethod
    def iter_sites(locations: Any) -> Iterable[dict]:
        """Sites are nested several levels deep, by state and then by city."""
        if isinstance(locations, dict):
            if "site_id" in locations:
                yield locations
                return
            for value in locations.values():
                yield from ZipsCarWashUSSpider.iter_sites(value)
        elif isinstance(locations, list):
            for value in locations:
                yield from ZipsCarWashUSSpider.iter_sites(value)

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()
        for day, open_time, close_time in re.findall(
            r'"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)":\s*"(\d{2}:\d{2})-(\d{2}:\d{2})"',
            response.text,
        ):
            oh.add_range(DAYS_EN[day], open_time, close_time)

        if oh:
            item["opening_hours"] = oh

        yield item
