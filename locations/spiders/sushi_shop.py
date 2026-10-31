import re
from typing import Any, AsyncIterator

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class SushiShopSpider(Spider):
    name = "sushi_shop"
    item_attributes = {"brand": "Sushi Shop", "brand_wikidata": "Q3505657"}
    domains = {
        "www.sushishop.fr": "FR",
        "www.sushishop.be": "BE",
        "www.sushishop.lu": "LU",
        "www.sushishop.eu": "ES",
        "www.mysushishop.ch": "CH",
        "www.mysushishop.co.uk": "GB",
    }

    async def start(self) -> AsyncIterator[Request]:
        for domain, country in self.domains.items():
            yield Request(
                f"https://{domain}/rollingstart/page-data/sq/d/3703147520.json",
                cb_kwargs={"domain": domain, "country": country},
            )

    def parse(self, response: Response, domain: str, country: str, **kwargs: Any) -> Any:
        seen = set()
        for store in response.json()["data"]["allStore"]["nodes"]:
            if not store["active"] or store["comming_soon"] or store["id_store"] in seen:
                continue
            seen.add(store["id_store"])
            store["street_address"] = merge_address_lines([store.pop("address"), store.pop("address2")])
            item = DictParser.parse(store)
            item["ref"] = "{}-{}".format(country, store["id_store"])
            item["branch"] = item.pop("name")
            item["country"] = country
            item["lat"] = store["gmap_latitude"]
            item["lon"] = store["gmap_longitude"]
            item["website"] = "https://{}{}".format(domain, store["uri"])
            if "826826" in re.sub(r"\D", "", item.get("phone") or ""):
                item.pop("phone")

            item["opening_hours"] = OpeningHours()
            for day, hours in zip(DAYS_FROM_SUNDAY, store["opening_hours"]):
                if (
                    hours["is_closed_am"] == "0"
                    and hours["is_closed_pm"] == "0"
                    and hours["time_closing_am"] == hours["time_opening_pm"]
                ):
                    item["opening_hours"].add_range(day, hours["time_opening_am"], hours["time_closing_pm"], "%H:%M:%S")
                    continue
                for half in ("am", "pm"):
                    if hours[f"is_closed_{half}"] == "0":
                        item["opening_hours"].add_range(
                            day, hours[f"time_opening_{half}"], hours[f"time_closing_{half}"], "%H:%M:%S"
                        )

            apply_yes_no(Extras.DELIVERY, item, store["accept_shipping"], False)
            yield item
