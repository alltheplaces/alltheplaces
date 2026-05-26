import json
from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.outdoor_supply_hardware_us import decode_email


class TotalToolsAUSpider(PlaywrightSpider):
    name = "total_tools_au"
    item_attributes = {"brand": "Total Tools", "brand_wikidata": "Q116779059"}
    allowed_domains = ["www.totaltools.com.au"]
    start_urls = ["https://www.totaltools.com.au/totaltools_storelocator/index/loadStoreRewrite"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in json.loads(response.xpath("//pre/text()").get())["storesjson"]:
            item = DictParser.parse(store)
            item["ref"] = store["storelocator_id"]
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.totaltools.com.au/" + store["rewrite_request_path"]
            yield scrapy.Request(url=item["website"], callback=self.parse_store_page, meta={"item": item})

    def parse_store_page(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["email"] = decode_email(response.xpath("//@data-cfemail").get(""))
        hours_raw = (
            " ".join(response.xpath('//div[@id="open_hour"]/div/table/tbody/tr/td/text()').getall())
            .replace("-", " ")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        oh = OpeningHours()
        for day in hours_raw:
            day[0] = day[0].split(":", 1)[0]
            if day[0] not in DAYS_EN:
                continue
            oh.add_range(DAYS_EN[day[0]], day[1], day[2], "%H:%M")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
