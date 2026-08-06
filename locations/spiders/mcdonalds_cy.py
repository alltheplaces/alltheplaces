import re
from typing import Any

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsCYSpider(PlaywrightSpider):
    name = "mcdonalds_cy"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.com.cy/locate"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for i in re.findall(
            r"var McDonald_s_\w+\s*=\s*(.*)",
            response.xpath('//script[contains(text(), "function distance(lat1, lng1, lat2, lng2)")]/text()').get(),
        ):
            location = chompjs.parse_js_object(i)
            item = DictParser.parse(location)
            item["branch"] = item.pop("name", "").removeprefix("McDonald's ")
            item["ref"] = location["key"]

            services = location["services_listed"]
            apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in services)
            apply_yes_no(Extras.TAKEAWAY, item, "takeaway" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "dinein" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "drivethru" in services)

            apply_category(Categories.FAST_FOOD, item)

            yield item
