from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class TheFragranceShopGBSpider(Spider):
    name = "the_fragrance_shop_gb"
    item_attributes = {"brand": "The Fragrance Shop", "brand_wikidata": "Q105337125"}
    start_urls = ["https://www.thefragranceshop.co.uk/api/stores/all"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["opening_hours"] = self.parse_hours(location.get("openingHours", ""))
            apply_category(Categories.SHOP_PERFUMERY, item)
            yield item

    def parse_hours(self, times: str) -> OpeningHours:
        # Seven comma-separated ranges, Monday first; a few stores prefix each range with its day name
        oh = OpeningHours()
        for day, part in zip(DAYS, (p.strip() for p in times.split(",") if p.strip())):
            if part.upper() == "CLOSED":
                oh.set_closed(day)
            elif sanitise_day(part.split()[0]):
                oh.add_ranges_from_string(part)
            else:
                oh.add_ranges_from_string(f"{day} {part}")
        return oh
