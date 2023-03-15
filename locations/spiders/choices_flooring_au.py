import html
import json

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ChoicesFlooringAUSpider(Spider):
    name = "choices_flooring_au"
    item_attributes = {"brand": "Choices Flooring", "brand_wikidata": "Q117155570"}
    allowed_domains = ["www.choicesflooring.com.au"]
    start_urls = [
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=1&filter='ALL'&mood=0", # ACT
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=2&filter='ALL'&mood=0", # WA
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=3&filter='ALL'&mood=0", # NSW
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=4&filter='ALL'&mood=0", # QLD
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=5&filter='ALL'&mood=0", # VIC
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=6&filter='ALL'&mood=0", # TAS
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=7&filter='ALL'&mood=0", # SA
        "https://www.choicesflooring.com.au/CMSPages/WebService.asmx/GetAllStoresByStateId?stateId=8&filter='ALL'&mood=0", # NT
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        locations = json.loads(html.unescape(response.json()["d"]))
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["StoreID"]
            item["addr_full"] = " ".join(location["Address"].replace("<br/>", "").split())
            item["website"] = "https://www.choicesflooring.com.au" + location["NodeAliasPath"]
            item["opening_hours"] = OpeningHours()
            hours_html = Selector(text=location["OpeningHours"])
            hours_raw = hours_html.xpath('//span[contains(@class, "st-day") or contains(@class, "st-time")]/text()').getall()
            hours_string = html.unescape(" ".join(hours_raw))
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
