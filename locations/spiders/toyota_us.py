from datetime import timedelta
from typing import Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(JSONBlobSpider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    locations_key = "dealers"

    def start_requests(self) -> Iterable[JsonRequest | Request]:
        # API can not handle huge radius coverage, therefore
        # I decicded to use zipcodes from:
        # Alaska(99775), Florida(33040), California(91932), Washington(98221), Kansas(66952), Maine(04619)
        for zip_code in ["99775", "33040", "91932", "98221", "66952", "04619"]:
            yield Request(
                url=f"https://api.ws.dpcmaps.toyota.com/v1/dealers?searchMode=pmaProximityLayered&radiusMiles=1000&resultsMax=5000&zipcode={zip_code}",
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        full_address = item.pop("addr_full")
        location = [item.strip() for item in full_address.split(",")]
        item["street_address"] = location[0]
        item["city"] = location[1]
        item["postcode"] = location[len(location) - 1].split(" ")[1]
        item["name"] = feature["label"]
        item["website"] = feature["details"]["uriWebsite"]
        self.parse_hours(item, feature["hoursOfOperation"])

        departments = feature["details"]["departmentInformation"]
        apply_category(Categories.SHOP_CAR, item)
        apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments)
        apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)

        yield item

    def parse_hours(self, item, hours_type):
        try:
            oh = OpeningHours()
            for day_times in hours_type:
                if "availabilityStartTimeMeasure" in day_times:
                    units_start = day_times["availabilityStartTimeMeasure"]["unitCode"]
                    units_end = day_times["availabilityEndTimeMeasure"]["unitCode"]
                    if units_start == "MINUTE" and units_end == "MINUTE":
                        oh.add_range(
                            day_times["dayOfWeekCode"][:2],
                            str(timedelta(minutes=day_times["availabilityStartTimeMeasure"]["value"])),
                            str(timedelta(minutes=day_times["availabilityEndTimeMeasure"]["value"])),
                            time_format="%H:%M:%S",
                        )
                    else:
                        self.crawler.stats.inc_value(f"atp/{self.name}/unknown_time_unit/{units_start}/{units_end}")
                else:
                    oh.set_closed(day_times["dayOfWeekCode"])

            if len(oh.day_hours) > 0:
                item["opening_hours"] = oh

        except Exception:
            self.crawler.stats.inc_value(f"atp/{self.name}/error_during_parse_hours/{item['ref']}")
