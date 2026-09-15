import json
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class StLouisBarAndGrillCASpider(JSONBlobSpider):
    name = "st_louis_bar_and_grill_ca"
    item_attributes = {"brand": "St. Louis Bar & Grill", "brand_wikidata": "Q65567668"}
    start_urls = ["https://locations.stlouiswings.com/"]

    def extract_json(self, response: Response) -> list[dict]:
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        return data["props"]["pageProps"]["locations"]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("store_code")
        location["street_address"] = merge_address_lines(
            [location.pop(f"address_line_{line}", None) for line in range(1, 5)]
        )
        location["phone"] = location.pop("formatted_phone", None)

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        item["website"] = location["canonical_url"]

        if open_date := location.get("open_date"):
            item["extras"]["start_date"] = open_date[:10]

        item["opening_hours"] = OpeningHours()
        for day in location.get("hours") or []:
            day_name = DAYS[day["day_of_week"] - 1]
            if day["is_closed"]:
                item["opening_hours"].set_closed(day_name)
            elif day["is_24_hours"]:
                item["opening_hours"].add_range(day_name, "00:00", "24:00")
            for interval in day["intervals"]:
                close_time = interval["close_time"]
                if interval["close_day_offset"] and close_time == "00:00":
                    close_time = "24:00"
                item["opening_hours"].add_range(day_name, interval["open_time"], close_time)

        apply_category(Categories.RESTAURANT, item)
        yield item
