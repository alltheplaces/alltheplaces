from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AvedaSpider(Spider):
    name = "aveda"
    item_attributes = {
        "brand": "Aveda",
        "brand_wikidata": "Q4827965",
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 100}

    async def start(self) -> AsyncIterator[Request]:
        url = "https://www.aveda.com/rpc/jsonrpc.tmpl?dbgmethod=locator.doorsandevents"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payload = 'JSONRPC=[{"method":"locator.doorsandevents","params":[{"fields":"ACTUAL_ADDRESS, ACTUAL_ADDRESS2, ACTUAL_CITY, STORE_TYPE, STATE, ZIP, DOORNAME, ADDRESS, ADDRESS2, CITY, STATE_OR_PROVINCE, ZIP_OR_POSTAL, COUNTRY, PHONE1, LONGITUDE, LATITUDE, LOCATION, WEBURL, EMAILADDRESS, APPT_URL","radius":"10200","latitude":48.9098994,"longitude":8.2499462,"uom":"miles"}]}]'
        yield Request(url=url, body=payload, method="POST", headers=headers, callback=self.parse)

    def parse(self, response):
        data = response.json()[0].get("result", {}).get("value", {}).get("results", {}).items()
        for key, value in data:
            item = DictParser.parse(value)
            item["ref"] = key
            item["name"] = value.get("DOORNAME")
            item["addr_full"] = None  # The DictParser puts street address in the wrong spot
            item["street_address"] = value.get("ACTUAL_ADDRESS")
            item["phone"] = value.get("PHONE1")
            item["website"] = value.get("WEBURL")

            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
