import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MuffinBreakAUSpider(Spider):
    name = "muffin_break_au"
    item_attributes = {"brand": "Muffin Break", "brand_wikidata": "Q16964876"}
    allowed_domains = ["muffinbreak.com.au"]
    start_urls = ["https://muffinbreak.com.au/wp-json/store-locator/v1/store/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("name", None)
            branch = " ".join(location["locname"].replace("&#8217;", "’").split())
            if "Croc" in branch:
                item["located_in"] = "Croc's Playcentre"
                branch = re.sub(r"Croc[’']?s Playcentre", "", branch)
            item["branch"] = re.sub(r"^Muffin Break\s*", "", branch).strip()
            item["addr_full"] = merge_address_lines([location["address"], location["address2"]])
            item["website"] = location["web"]
            apply_category(Categories.CAFE, item)

            hours_raw = "; ".join(
                f'{rule["days"]} {rule["hours"]}' for rule in location["opening_hours"] or [] if rule["hours"]
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                hours_raw.replace("Open 7 Days", "Mo-Su")
                .replace("Thrusday", "Thursday")
                .replace("Wedensday", "Wednesday")
                .replace("4.00pm", "4:00pm")
                .replace("8:300pm", "8:30pm")
            )
            yield item
