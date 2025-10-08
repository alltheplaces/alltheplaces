from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class FustCHSpider(JSONBlobSpider):
    name = "fust_ch"
    item_attributes = {
        "brand": "Fust",
        "brand_wikidata": "Q1227164",
        "country": "CH",
    }
    start_urls = ["https://www.fust.ch/store-finder"]

    def extract_json(self, response: Response) -> list[dict]:
        location_data = response.xpath('//script[contains(text(), "pointOfService")]/text()').get()
        return [
            chompjs.parse_js_object(location, unicode_escape=True)
            for location in location_data.split(r"{\"pointOfService\":")[1:]
        ]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))
        if contact_info := feature.get("contactDetails"):
            feature.update(contact_info[0])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([feature.get("line1"), feature.get("line2")])
        item["branch"] = item.pop("name").replace("-", " ").title().removesuffix(" Center")
        item["website"] = response.urljoin(feature["url"].split("?")[0].replace("/store/", "/store-finder/"))
        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openingHours", {}).get("weekDayOpeningList", []):
            if day := sanitise_day(rule["weekDay"].replace(".", ""), DAYS_DE):
                if rule.get("closed"):
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(
                        day, rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"]
                    )

        yield item
