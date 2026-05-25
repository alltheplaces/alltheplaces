import json
import re
from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class NeonetPLSpider(Spider):
    name = "neonet_pl"
    item_attributes = {"brand": "Neonet", "brand_wikidata": "Q11790622"}
    start_urls = ["https://www.neonet.pl/kontakt"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(re.search(r"salons\":(\[.+\]),\"navigation", response.text).group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines(location["address"]["lines"])
            item["website"] = urljoin("https://www.neonet.pl/kontakt/", location["safetyName"])

            oh = OpeningHours()
            oh.add_ranges_from_string(merge_address_lines(location["openHours"]), DAYS_PL)
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_ELECTRONICS, item)

            yield item
