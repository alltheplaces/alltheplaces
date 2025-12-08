from typing import Any, AsyncIterator

import chompjs
from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import FIREFOX_LATEST


class GucciSpider(Spider):
    name = "gucci"
    item_attributes = {"brand": "Gucci", "brand_wikidata": "Q178516"}
    is_playwright_spider = True
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST} | DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.gucci.com/int/en/store/all?south=-90&west=-180&north=90&east=180&latitude=0&longitude=0",
            headers={"Referer": "https://www.gucci.com/int/en/store?store-search=&search-cat=store-locator"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.text)["features"]:
            if location["properties"]["active"] is not True:
                continue
            item = DictParser.parse(location["properties"])
            item["website"] = "https://www.gucci.com/int/en{}".format(item["website"])
            item["ref"] = location["properties"]["storeCode"]
            item["street_address"] = location["properties"]["address"]["location"]
            item["phone"] = location["properties"]["address"]["phone"]
            self.crawler.stats.inc_value("z/type/{}".format(location["properties"]["type"]))

            yield item
