import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.pipelines.address_clean_up import merge_address_lines


class PriceriteUSSpider(scrapy.Spider):
    name = "pricerite_us"
    item_attributes = {"brand": "PriceRite", "brand_wikidata": "Q7242560"}
    allowed_domains = ["priceritemarketplace.com"]
    start_urls = ("https://www.priceritemarketplace.com/",)
    requires_proxy = True

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').extract_first()
        script = script[script.index("{") :]
        stores = json.loads(script)["stores"]["availablePlanningStores"]["items"]

        for store in stores:
            store["street_address"] = merge_address_lines(
                [store["addressLine1"], store["addressLine2"], store["addressLine3"]]
            )
            store["state"] = store["countyProvinceState"]
            item = DictParser.parse(store)
            item["ref"] = store["retailerStoreId"]
            item["website"] = f'https://www.priceritemarketplace.com/sm/planning/rsid/{item["ref"]}'

            item["opening_hours"] = OpeningHours()
            for start_day, end_day, start_time, start_zone, end_time, end_zone in re.findall(
                r"(\w+)(?:\s*-\s*(\w+))?:? (\d+)\s*([ap]m)\s*-\s*(\d+)\s*([ap]m)",
                store["openingHours"].replace("\\n", " ").replace(" to ", "-"),
            ):
                if not end_day:
                    end_day = start_day
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day),
                    f"{start_time}{start_zone}",
                    f"{end_time}{end_zone}",
                    time_format="%I%p",
                )

            yield item
