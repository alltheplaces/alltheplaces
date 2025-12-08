import re

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

name_match = re.compile(r"^Big 5 Sporting Goods #(?P<ref>\d+)\s*[-–]\s*(?P<branch>.*)$")


class Big5SportingGoodsUSSpider(Spider):
    name = "big_5_sporting_goods_us"
    item_attributes = {"brand": "Big 5 Sporting Goods", "brand_wikidata": "Q4904902"}
    start_urls = ["https://www.big5sportinggoods.com/store/integration/find_a_store.jsp?miles=25000&lat=0&lng=0"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for store in response.xpath("//div[@class='store-add-wrrper']"):
            location = {
                inp.attrib["name"].removesuffix("Hidden"): inp.attrib["value"]
                for inp in store.xpath(".//input")
                if "name" in inp.attrib
            }
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")

            name = item.pop("name")
            try:
                item.update(name_match.match(name).groupdict())
            except AttributeError:
                self.logger.error(name)

            oh = OpeningHours()
            for day in DAYS_FULL:
                hours = location[f"regularHours{day}"]
                oh.add_ranges_from_string(f"{day} {hours}")
            item["opening_hours"] = oh

            yield item
