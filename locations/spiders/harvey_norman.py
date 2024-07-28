import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address


class HarveyNormanSpider(Spider):
    name = "harvey_norman"
    item_attributes = {"brand": "Harvey Norman", "brand_wikidata": "Q4040441"}
    allowed_domains = ["stores.harveynorman.com.au", "stores.harveynorman.co.nz"]
    start_urls = ["https://stores.harveynorman.com.au/", "https://stores.harveynorman.co.nz/"]
    # There is no robots.txt, instead the store finder page (HTML)
    # is returned and this confuses Scrapy.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        for location in json.loads(data_raw)["props"]["pageProps"]["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = clean_address(location["addressLines"])
            if ".co.nz" in response.url:
                item.pop("state")
            if len(location["phoneNumbers"]) > 0:
                item["phone"] = location["phoneNumbers"][0]
            item["opening_hours"] = OpeningHours()
            for day_number, hours in enumerate(location["businessHours"]):
                if len(hours) < 2:
                    continue
                item["opening_hours"].add_range(DAYS[day_number - 1], hours[0], hours[1])
            yield item
