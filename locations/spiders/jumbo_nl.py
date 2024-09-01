import html
import re
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class JumboNLSpider(CrawlSpider):
    name = "jumbo_nl"
    item_attributes = {"brand": "Jumbo", "brand_wikidata": "Q2262314"}
    start_urls = ["https://www.jumbo.com/winkel"]
    allowed_domains = ["www.jumbo.com"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"/winkel/",
                deny=["city", "foodmarkt"],
                tags=["jum-list-item"],
                attrs=["link"],
            ),
            callback="parse",
        ),
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
    }

    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = chompjs.parse_js_object(html.unescape(re.search(r"stores=\"(\[.*\])\"", response.text).group(1)))
        for store in data:
            store.update(store["location"].pop("address"))
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                time = store["openingHours"][day.lower()]
                if open_time := time["open"]:
                    open_time = open_time.replace(":00.000Z", "")
                if close_time := time["close"]:
                    close_time = time["close"].replace(":00.000Z", "")
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item
