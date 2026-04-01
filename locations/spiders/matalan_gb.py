import json
import re
from typing import Any

from requests import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class MatalanGBSpider(SitemapSpider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    allowed_domains = ["www.matalan.co.uk"]
    sitemap_urls = ["https://www.matalan.co.uk/robots.txt"]
    sitemap_rules = [(r"/stores/uk/[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"storeData\s*=\s*({.*});\s*const\s*nearbyStores",
                response.xpath('//*[@data-track="storeVisit"]//text()').get(),
            ).group(1)
        )
        raw_data.update(raw_data.pop("address"))
        item = DictParser.parse(raw_data)
        item["branch"] = item.pop("name").replace("Matalan - ", "")
        item["website"] = response.url
        item["addr_full"] = merge_address_lines(
            [
                raw_data["addressLine1"],
                raw_data["addressLine2"],
                raw_data["addressLine3"],
                raw_data["addressLine4"],
                raw_data["addressLine5"],
            ]
        )
        oh = OpeningHours()
        try:
            for day_time in raw_data["openingTimes"]:
                day = day_time["day"]
                open_time = day_time["openingTime"][0:5]
                close_time = day_time["closingTime"][0:5]
                if open_time == "00:00" and close_time == "00:00":
                    oh.set_closed(day)
                else:
                    oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")
        except:
            pass
        item["opening_hours"] = oh
        yield item
