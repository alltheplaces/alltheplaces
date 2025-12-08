from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MobelBossDESpider(JSONBlobSpider):
    name = "mobel_boss_de"
    item_attributes = {"brand": "Möbel Boss", "brand_wikidata": "Q99624217"}
    start_urls = ["https://moebel-boss.de/api/v1/storefinder/boss/stores"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["key"] == "bossOnline":
            item["branch"] = item.pop("name")
            item["street_address"] = feature["streetNameAndNumber"]
            item["website"] = response.urljoin(feature["url"])
            item["image"] = response.urljoin(feature["image"])
            item["opening_hours"] = OpeningHours()

            for rule in feature["openingTime"]:
                if rule["openingTimesRemark"]:
                    continue  # "special opening time"
                if day := sanitise_day(rule["weekDay"], DAYS_DE):
                    if rule["closed"] is True:
                        item["opening_hours"].set_closed(day)
                    else:
                        item["opening_hours"].add_range(
                            day, rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"]
                        )
            apply_category(Categories.SHOP_FURNITURE, item)
            yield item
