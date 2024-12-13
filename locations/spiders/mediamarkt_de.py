import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MediamarktDESpider(scrapy.Spider):
    name = "mediamarkt_de"
    item_attributes = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}

    def start_requests(self):
        url = "https://www.mediamarkt.de/api/v1/graphql?operationName=AllStores&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2260c474a136d174045108cc578a0c99621e9eea0b3ae26d2c30f2fdfee410abb5%22%7D%2C%22pwa%22%3A%7B%22captureChannel%22%3A%22DESKTOP%22%2C%22salesLine%22%3A%22Media%22%2C%22country%22%3A%22DE%22%2C%22language%22%3A%22de%22%2C%22globalLoyaltyProgram%22%3Atrue%2C%22isOneAccountProgramActive%22%3Atrue%2C%22isMdpActive%22%3Atrue%7D%7D"
        headers = {
            "x-operation": "AllStores",
            "x-cacheable": "true",
            "apollographql-client-version": "8.129.1",
            "content-type": "application/json",
        }
        yield JsonRequest(url=url, headers=headers)

    def parse(self, response: Response, **kwargs):
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day_time in store["openingTimes"]["regular"]:
                day = day_time["type"]
                open_time = day_time["start"]
                close_time = day_time["end"]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item
