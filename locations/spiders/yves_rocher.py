import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class YvesRocherSpider(Spider):
    name = "yves_rocher"
    item_attributes = {"brand": "Yves Rocher", "brand_wikidata": "Q1477321"}
    start_urls = [
        "https://www.yves-rocher.fr/magasins-instituts-de-beaute/SL",
        "https://www.yves-rocher.es/encuentra-tu-tienda/SL",
    ]
    requires_proxy = True
    # Zyte gets a "Website Ban" with the default bot user agent.
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        yield from response.follow_all(css="#all-store-container a[href*='/S-']", callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        if not (data := response.css("[data-woosmap-component]::attr(data-woosmap-component)").get()):
            return
        location = json.loads(data)
        # Head-office entries (e.g. "VAD" mail order in ES) have no coordinates and aren't shops.
        if location["location"] == [0, 0]:
            return
        location["lon"], location["lat"] = location.pop("location")
        location["street_address"] = merge_address_lines(
            [location.pop("address1", None), location.pop("address2", None)]
        )
        item = DictParser.parse(location)

        item["ref"] = location["storeId"]
        item["branch"] = item.pop("name", None)
        # The Andorra store is listed on the Spanish site as "YR-ES".
        if (location.get("zipCode") or "").startswith("AD"):
            item["country"] = "AD"
        else:
            item["country"] = location["countryCode"].removeprefix("YR-")
        item["website"] = response.url

        # Status 2 stores show "Fermé" every day on their page, whatever their opening fields say.
        if location.get("status") == 2:
            set_closed(item)
        else:
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if rule := location.get(f"opening{day}"):
                    for start_time, end_time in re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", rule):
                        item["opening_hours"].add_range(day, start_time, end_time)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
