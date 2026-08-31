import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MattressWarehouseUSSpider(CrawlSpider):
    name = "mattress_warehouse_us"
    BRANDS = {
        "mattress_warehouse": {"brand": "Mattress Warehouse", "brand_wikidata": "Q61995079"},
        "sleep_outfitters": {"brand": "Sleep Outfitters", "brand_wikidata": "Q120509459"},
    }
    start_urls = ["https://mattresswarehouse.com/store-locator"]

    rules = [
        Rule(
            LinkExtractor(allow=r"/store-locator/mattress-stores-in"),
            callback="parse",
            follow=True,
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if raw_data := response.xpath('//*[contains(text(),"postalCode")]/text()').get():
            for location in json.loads(
                re.search(r"locationDetails\"\s*:\s*(\[.*\]),\"cityStateSlug", raw_data).group(1)
            ):
                item = DictParser.parse(location)
                item["addr_full"] = location["addressMetafield"]
                item["branch"] = (
                    item.pop("name").replace("Mattress Warehouse of ", "").replace("Sleep Outfitters of ", "")
                )
                brand_slug = re.search(r"(.+\s*of)\s*", location["name"]).group(1).lower().replace(" ", "-")
                branch_slug = location["nameMetafield"].replace(" ", "_").replace(",", "").lower()
                item["website"] = response.url.replace(
                    "mattress-stores-in", "-".join([brand_slug, branch_slug, item["ref"]])
                )
                if "Sleep Outfitters" in location["name"]:
                    item.update(self.BRANDS["sleep_outfitters"])
                else:
                    item.update(self.BRANDS["mattress_warehouse"])
                oh = OpeningHours()
                for day, time in location["hours"].items():
                    day = day
                    open_time = time["start"]
                    close_time = time["end"]
                    oh.add_range(day, open_time, close_time)
                item["opening_hours"] = oh
                yield item
