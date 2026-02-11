import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WestpacNZSpider(Spider):
    name = "westpac_nz"
    item_attributes = {"brand": "Westpac", "brand_wikidata": "Q2031726"}
    start_urls = ["https://www.westpac.co.nz/contact-us/branch-finder/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = "NZ"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//div[@class="js-branch-finder-map container"]/@data-props').get())[
            "branches"
        ]:
            item = DictParser.parse(location)
            item["branch"] = location["siteName"]
            item["ref"] = location["key"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                hours_key = "{}Hours".format(day.lower())
                if location[hours_key] == "Closed":
                    item["opening_hours"].set_closed(day)
                elif "24/7" in location[hours_key]:
                    item["opening_hours"] = "24/7"
                    break
                elif location[hours_key] == "Open limited hours":
                    pass
                else:
                    open_time, closed_time = location[hours_key].split(" - ")
                    item["opening_hours"].add_range(day, open_time, closed_time, "%H:%M%p")
            match location["locationType"]:
                case "Branch":
                    apply_category(Categories.BANK, item)
                case "ATM":
                    apply_category(Categories.ATM, item)
            yield item
