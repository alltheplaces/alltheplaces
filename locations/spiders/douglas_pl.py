import json
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class DouglasPLSpider(PlaywrightSpider):
    name = "douglas_pl"
    item_attributes = {"brand": "Douglas", "brand_wikidata": "Q2052213"}
    allowed_domains = ["www.douglas.pl"]
    start_urls = ["https://www.douglas.pl/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in json.loads(response.xpath("//pre//text()").get()).get("stores"):
            data.update(data.pop("address"))
            data["id"] = data.pop("name")
            item = DictParser.parse(data)
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            item["website"] = "https://{}{}".format(self.allowed_domains[0], data.pop("url"))
            apply_category(Categories.SHOP_PERFUMERY, item)
            item["opening_hours"] = OpeningHours()
            for day_hours in data["openingHours"]["weekDayOpeningList"]:
                day_abbrev = DAYS_PL[day_hours["weekDayFull"].title()]
                if day_hours["closed"]:
                    item["opening_hours"].set_closed(day_abbrev)
                else:
                    item["opening_hours"].add_range(
                        day_abbrev, day_hours["openingTime"]["formattedHour"], day_hours["closingTime"]["formattedHour"]
                    )

            yield item
