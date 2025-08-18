from typing import Any, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CostcoCASpider(Spider):
    name = "costco_ca"
    item_attributes = {"brand": "Costco", "brand_wikidata": "Q715583"}
    start_urls = ["https://www.costco.ca/AjaxWarehouseBrowseLookupView?countryCode=CA"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    }

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url="https://www.costco.ca/AjaxWarehouseBrowseLookupView?countryCode=CA",
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in chompjs.parse_js_object(response.text):  # JSON is embedded within HTML
            if not isinstance(store, dict):
                continue
            item = DictParser.parse(store)
            item["ref"] = item.pop("name")
            item["branch"] = store["locationName"]
            item["website"] = (
                "https://www.costco.ca/warehouse-locations/"
                + "-".join([item["branch"].replace(" ", "-"), item["state"], str(item["ref"])])
                + ".html"
            )
            apply_category(Categories.SHOP_WHOLESALE, item)

            if store["hasBusinessDepartment"] is True:
                item["name"] = "Costco Business Center"
            else:
                item["name"] = "Costco"

            yield item
