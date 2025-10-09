from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MondadoriITSpider(JSONBlobSpider):
    name = "mondadori_it"
    BRANDS = {
        "Mondadori": ("Mondadori", "Q85355"),
        "Rizzoli": ("Rizzoli", "Q1327389"),
        "Mondolibri": ("Mondolibri", "Q119942453"),
    }
    start_urls = [
        "https://www.mondadoristore.it/occ/v2/mondadorisite-b2c/stores?pageSize=1000&currentPage=0&province=&latitude=45.4642&longitude=9.19&fields=FULL&lang=it&curr=EUR"
    ]
    locations_key = "results"
    needs_json_request = True

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["state"] = feature.get("region", {}).get("isocode")
        item["ref"] = item.pop("name")
        location_name = feature.get("displayName", "").title()
        item["branch"] = (
            location_name.removeprefix("Mondadori Bookstore").removeprefix("Mondadori Point").strip("").strip("- ")
        )
        location_type = "point" if "Point" in location_name else "bookstore"
        item["website"] = (
            f'https://www.mondadoristore.it/negozi/libreria/mondadori-{location_type}-{item["city"].lower().replace(" ", "-")}/{item["ref"]}'
        )

        if location_type == "point":
            apply_category(Categories.SHOP_NEWSAGENT, item)
        else:
            apply_category(Categories.SHOP_BOOKS, item)

        for brand in self.BRANDS:
            if brand in location_name:
                item["brand"], item["brand_wikidata"] = self.BRANDS.get(brand)

        try:
            item["opening_hours"] = OpeningHours()
            hours = feature.get("openingHours", {}).get("weekDayOpeningList", [])
            for rule in hours:
                if day := sanitise_day(rule.get("weekDay"), DAYS_IT):
                    if rule.get("closed"):
                        item["opening_hours"].set_closed(day)
                    else:
                        for shift in rule.get("openingSchedule", []):
                            if opening := shift["openingTime"].get("formattedHour"):
                                if closing := shift["closingTime"].get("formattedHour"):
                                    item["opening_hours"].add_range(day, opening, closing)
        except:
            self.logger.error("Failed to parse opening hours: {}".format(hours))
        yield item
