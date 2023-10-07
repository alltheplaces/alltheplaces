from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DelikatesyCentrumPLSpider(Spider):
    name = "delikatesy_centrum_pl"
    item_attributes = {"brand": "Delikatesy Centrum", "brand_wikidata": "Q11693824"}
    start_urls = ["https://www.delikatesy.pl"]
    allowed_domains = ["www.delikatesy.pl"]

    def start_requests(self):
        yield JsonRequest(url=self.start_urls[0])

    def parse(self, response):
        nextBuildId = response.xpath("//script[contains(@src, '_ssgManifest.js')]/@src").get().split("/")[3]
        url = f"https://www.delikatesy.pl/_next/data/{nextBuildId}/sklepy.json"
        yield JsonRequest(url=url, callback=self.parse_api)

    def parse_api(self, response):
        for location in response.json()["pageProps"]["shops"]:
            item = DictParser.parse(location)
            item["ref"] = location["shop_code"]
            item["name"] = location["name"].split("\\", 1)[0].strip()
            item["lat"] = location["address"]["lat"]
            item["lon"] = location["address"]["lon"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["opening_hours"]:
                if not day_hours["hours"] or day_hours["hours"] == "czynne":
                    continue
                item["opening_hours"].add_range(day_hours["day"].title(), *day_hours["hours"].split("-", 1), "%H:%M")
            yield item
