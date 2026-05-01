import json
from typing import Any

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class DfsGBSpider(PlaywrightSpider):
    name = "dfs_gb"
    item_attributes = {"brand": "DFS", "brand_wikidata": "Q5204927"}
    start_urls = ["https://www.dfs.co.uk/wcs/resources/store/10202/stores?langId=-1"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath("//pre/text()").get())
        for location in data["stores"]:
            item = DictParser.parse(location)
            item["phone"] = None
            item["branch"] = item.pop("name").removeprefix("DFS ")
            item["street_address"] = merge_address_lines([location["address"]["line1"], location["address"]["line2"]])
            item["lat"] = location["yextRoutableCoordinate"]["latitude"]
            item["lon"] = location["yextRoutableCoordinate"]["longitude"]
            item["opening_hours"] = self.parse_opening_hours(location["hours"])
            item["website"] = "https://www.dfs.co.uk/store-directory/{}".format(location["seoToken"])
            item["image"] = "https://images.dfs.co.uk/i/dfs/{}".format(
                location["storeImageName"].replace("?$store_ss$", "")
            )

            apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Access" in location["services"])

            yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in rules.items():
            if rule["closed"] is True:
                oh.set_closed(day)
            else:
                for times in rule["openIntervals"]:
                    oh.add_range(day, times["start"], times["end"])

        return oh
