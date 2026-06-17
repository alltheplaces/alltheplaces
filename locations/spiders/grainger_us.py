from typing import Any, AsyncIterator

import chompjs
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class GraingerUSSpider(PlaywrightSpider):
    name = "grainger_us"
    item_attributes = {"brand": "Grainger", "brand_wikidata": "Q1627894"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["US"], 315):
            yield JsonRequest(
                url=f"https://www.grainger.com/rservices/branch/find/12/1?searchBox=us&latitude={lat}&longitude={lon}&miles=200",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.text).get("payload", {}).get("branches", []):
            location.update(location.pop("branchAddress"))
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
            item["ref"] = location["branchCode"]
            item["branch"] = location["branchURL"].split("-Branch")[0].split("/")[-1].replace("-", " ")
            item["phone"] = item["phone"].split("GRAINGER")[-1] if item.get("phone") else None
            item["extras"]["fax"] = location.get("fax")
            item["website"] = response.urljoin(location["branchURL"].replace(" ", "%20"))
            yield item
