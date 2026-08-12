import json
from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NeonetPLSpider(JSONBlobSpider):
    name = "neonet_pl"
    item_attributes = {"brand": "Neonet", "brand_wikidata": "Q11790622"}
    start_urls = ["https://www.neonet.pl/kontakt"]

    def extract_json(self, response: Response) -> Any:
        marker = "window.__INITIAL_STATE__['app'] = "
        start = response.text.index(marker) + len(marker)
        return json.JSONDecoder().raw_decode(response.text[start:])[0].get("salons", [])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = ", ".join(feature["address"].get("lines") or [])
        item["website"] = urljoin("https://www.neonet.pl/kontakt/", feature["safetyName"])

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openHoursStructured") or []:
            for day_of_week in rule.get("dayOfWeek") or []:
                item["opening_hours"].add_range(
                    DAYS[day_of_week - 1], rule["openHour"], rule["closeHour"], time_format="%H:%M:%S"
                )

        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
