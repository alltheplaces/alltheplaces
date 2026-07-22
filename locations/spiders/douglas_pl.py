import json
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.douglas_de import DOUGLAS_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class DouglasPLSpider(PlaywrightSpider):
    name = "douglas_pl"
    item_attributes = DOUGLAS_SHARED_ATTRIBUTES
    allowed_domains = ["www.douglas.pl"]
    start_urls = ["https://www.douglas.pl/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in json.loads(response.xpath("//pre//text()").get()).get("stores"):
            data.update(data.pop("address"))
            item = DictParser.parse(data)
            item["phone"] = None
            item["ref"] = item.pop("name")
            item["branch"] = data.get("displayName")
            item["website"] = response.urljoin(data.get("url"))

            apply_category(Categories.SHOP_PERFUMERY, item)

            item["opening_hours"] = OpeningHours()
            for day_hours in data["openingHours"]["weekDayOpeningList"]:
                day_abbrev = DAYS[day_hours["dayOfWeek"] - 1]
                if day_hours["closed"]:
                    item["opening_hours"].set_closed(day_abbrev)
                else:
                    item["opening_hours"].add_range(
                        day_abbrev, day_hours["openingTime"]["formattedHour"], day_hours["closingTime"]["formattedHour"]
                    )

            yield item
