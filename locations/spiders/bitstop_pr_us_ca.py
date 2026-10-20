from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BitstopPRUSCASpider(JSONBlobSpider):
    name = "bitstop_pr_us_ca"
    allowed_domains = ["account.bitstop.co"]
    start_urls = ["https://account.bitstop.co/api/a/v2/map/locations"]
    locations_key = "data"
    item_attributes = {"brand": "Bitstop", "brand_wikidata": "Q135316538"}
    country_codes = {"USA": "US", "Canada": "CA"}
    operator_wikidata = {
        "ATM OPS, Inc.": "Q135316538",
        "Express BTM, LLC.": "Q135316892",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.start_urls[0],
            method="POST",
            data={"lat": 0, "lng": 0, "page": 1, "page_size": 5000, "filter": ""},
        )

    def pre_process_data(self, feature: dict) -> None:
        if country := feature.get("country"):
            feature["country"] = self.country_codes.get(country, country)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item.pop("phone", None)

        if located_in := feature.get("location_name"):
            item["located_in"] = located_in

        if operator_name := feature.get("operated_by"):
            item["operator"] = operator_name
            if wikidata := self.operator_wikidata.get(operator_name):
                item["operator_wikidata"] = wikidata

        if images := feature.get("images"):
            item["image"] = images[0]

        if hours_array := feature.get("hours"):
            # Placeholder value seen when a location's actual hours are unconfirmed
            if set(hours_array) != {"12:00 AM - 1:00 AM, 12:00 PM - 1:00 PM"}:
                item["opening_hours"] = OpeningHours()
                for day, hours in zip(DAYS, hours_array):
                    if hours == "-":
                        item["opening_hours"].set_closed(day)
                    elif hours == "24/7":
                        item["opening_hours"].add_range(day, "00:00", "24:00")
                    else:
                        open_time, close_time = hours.split(" - ")
                        item["opening_hours"].add_range(day, open_time, close_time, "%I:%M %p")

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        match item.get("country"):
            case "CA":
                item["extras"]["currency:CAD"] = "yes"
            case "US" | "PR":
                item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"

        if place_id := feature.get("place_id"):
            item["extras"]["ref:google:place_id"] = place_id

        yield item
