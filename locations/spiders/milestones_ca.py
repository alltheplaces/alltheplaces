from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MilestonesCASpider(StructuredDataSpider):
    name = "milestones_ca"
    item_attributes = {"brand": "Milestones", "brand_wikidata": "Q6851623"}
    start_urls = ["https://milestonesrestaurants.com/all-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for path in set(response.xpath('//a[contains(@href, "/locations/")]/@href').getall()):
            yield response.follow(path, self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item.pop("twitter", None)
        item.pop("facebook", None)

        item["opening_hours"] = OpeningHours()
        for rule in ld_data.get("openingHoursSpecification") or []:
            if rule.get("opens") and rule.get("closes"):
                for day in rule["dayOfWeek"].split(","):
                    item["opening_hours"].add_range(day.strip(), rule["opens"], rule["closes"])

        apply_category(Categories.RESTAURANT, item)
        yield item
