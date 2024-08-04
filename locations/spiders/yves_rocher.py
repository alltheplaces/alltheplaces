import json
import re
from urllib.parse import urljoin

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class YvesRocherSpider(CrawlSpider):
    name = "yves_rocher"
    item_attributes = {"brand": "Yves Rocher", "brand_wikidata": "Q28496595"}
    start_urls = ["https://www.yves-rocher.es/encuentra-tu-tienda/SL"]
    rules = [Rule(LinkExtractor(allow=r"https://www.yves.+?/.+?/SL", tags="link"), callback="parse")]
    requires_proxy = True

    def parse(self, response, **kwargs):
        data = json.loads(
            json.loads(
                re.search(
                    r"data = JSON.parse\((.+)\);",
                    response.xpath('//script[contains(text(), "data = JSON.parse(")]/text()').get(),
                ).group(1)
            )
        )
        for location in DictParser.get_nested_key(data, "allStores"):
            location["lon"], location["lat"] = location.pop("location")
            location.pop("countryCode")
            location["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if rule := location.get(f"opening{day}"):
                    for start_time, end_time in re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", rule):
                        item["opening_hours"].add_range(day, start_time, end_time)

            item["website"] = urljoin(response.url, location["uri"])

            apply_category(Categories.SHOP_BEAUTY, item)

            yield item
