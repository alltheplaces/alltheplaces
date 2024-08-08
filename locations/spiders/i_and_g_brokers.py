from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class IAndGBrokersSpider(Spider):
    name = "i_and_g_brokers"
    item_attributes = {"brand": "I&G Brokers", "brand_wikidata": "Q110399829"}
    allowed_domains = ["iandgbrokers.com"]
    start_urls = ["https://iandgbrokers.com/offices/pins?srch_offices=&city=&features[]=all&_=1695470505675"]

    def parse(self, response):
        for data in response.json()["markers"]["offices"]:
            data = data["data"]
            item = DictParser.parse(data)

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(data["worktime"], days=DAYS_BG)

            yield item
