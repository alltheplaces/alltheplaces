import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class WaffleHouseUSSpider(Spider):
    name = "waffle_house_us"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    allowed_domains = ["wafflehouse.com"]
    start_urls = ["https://locations.wafflehouse.com/regions"]
    # robots.txt returns the HTML for the store locator page which confuses Scrapy
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        locations_text = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = json.loads(locations_text)["props"]["pageProps"]["locations"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = clean_address(location["addressLines"])
            if len(location["phoneNumbers"]) > 0:
                item["phone"] = location["phoneNumbers"][0]
            item["website"] = item["website"].replace("///", "/")
            yield item
