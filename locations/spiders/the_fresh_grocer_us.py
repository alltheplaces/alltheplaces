import re

import chompjs

from locations.categories import Categories
from locations.hours import OpeningHours, day_range
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class TheFreshGrocerUSSpider(JSONBlobSpider):
    name = "the_fresh_grocer_us"
    item_attributes = {
        "brand": "The Fresh Grocer",
        "brand_wikidata": "Q18389721",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.thefreshgrocer.com/"]
    requires_proxy = True

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').get()
        )["stores"]["availablePlanningStores"]["items"]

    def pre_process_data(self, location):
        location["street_address"] = merge_address_lines(
            [location["addressLine1"], location["addressLine2"], location["addressLine3"]]
        )
        location["state"] = location["countyProvinceState"]

    def post_process_item(self, item, response, location):
        item["ref"] = location["retailerStoreId"]
        item["website"] = f'https://www.thefreshgrocer.com/sm/planning/rsid/{item["ref"]}'

        if "openingHours" in location and location["openingHours"] is not None:
            if m := re.search(
                r"(\w+)(?: (?:-|thru) (\w+))?: (\d+)\s*([ap]m) (?:-|to) (\d+)\s*([ap]m)",
                location["openingHours"],
                re.IGNORECASE,
            ):
                start_day, end_day, start_time, start_zone, end_time, end_zone = m.groups()
                if not end_day:
                    end_day = start_day
                if start_day and end_day:
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day),
                        f"{start_time}{start_zone}",
                        f"{end_time}{end_zone}",
                        time_format="%I%p",
                    )

        yield item
