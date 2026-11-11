import json
import re

from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class FootasylumGBSpider(PlaywrightSpider):
    name = "footasylum_gb"
    item_attributes = {"brand": "Footasylum", "brand_wikidata": "Q126913565"}
    start_urls = ["https://www.footasylum.com/store-locator/"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: TextResponse):
        json_data = json.loads(
            re.search(
                r"stores\":(\[.*\]),\"global\"",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for store in json_data:
            item = DictParser.parse(store)
            item["addr_full"] = merge_address_lines(store.get("location").get("address"))
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(item.get("website"))
            yield item
