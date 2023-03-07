import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KFCMYSpider(scrapy.Spider):
    name = "kfc_my"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    allowed_domains = ["kfc.com.my"]
    start_urls = ["https://kfc.com.my/graphql?query=query+allLocation%7BallLocation%7Blocations%7Baddress+city+code+coleslaw+country+created+curbside+delivery_close+delivery_open+delivery_tier+dinein+drivethru+gesStoreId+is_breakfast+is_delivery+is_selfcollect+lat+launch_date+legacy_store_id+locationId+long+name+phone+riderType+selfcollect_close+selfcollect_open+selfcollect_tier+polygon+smartbox+state+storeCmgId+storeName+updated+zip+disabled_skus+is_breakfast+coleslaw+drivethru+smartbox+dinein+__typename%7D__typename%7D%7D&operationName=allLocation&variables=%7B%7D"]

    def parse(self, response):
        for location in response.json()["data"]["allLocation"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["locationId"]
            oh = OpeningHours()
            for day in DAYS:
                if len(location["selfcollect_open"].split(":")) == 2:
                    location["selfcollect_open"] = location["selfcollect_open"] + ":00"
                if len(location["selfcollect_close"].split(":")) == 2:
                    location["selfcollect_close"] = location["selfcollect_close"] + ":00"
                if location["selfcollect_close"] == "24:00:00":
                    location["selfcollect_close"] = "23:59:00"
                oh.add_range(day, location["selfcollect_open"], location["selfcollect_close"], "%H:%M:%S")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
