from typing import Any
from urllib.parse import urljoin

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

BARGAIN_BUYS = {"brand": "Bargain Buys", "brand_wikidata": "Q19870995"}
POUNDSTRETCHER = {"brand": "Poundstretcher", "brand_wikidata": "Q7235675"}


class PoundstretcherGBSpider(Spider):
    name = "poundstretcher_gb"
    item_attributes = POUNDSTRETCHER
    start_urls = ["https://www.poundstretcher.co.uk/ustorelocator/location/searchJson/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["markers"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = location["address_display"]
            item["website"] = urljoin("https://www.poundstretcher.co.uk/", location["website_url"])

            if item["branch"].endswith(" Bargain Buys"):
                item["branch"] = item["branch"].removesuffix(" Bargain Buys")
                item.update(BARGAIN_BUYS)

            try:
                sel = Selector(text=location["notes"])
                oh = OpeningHours()
                for rule in sel.xpath("//tr"):
                    times = rule.xpath("./td/text()").get()
                    start_time, end_time = times.split("-")
                    oh.add_range(rule.xpath("./th/text()").get(), start_time.strip(), end_time.strip())
                item["opening_hours"] = oh
            except:
                pass

            yield item
