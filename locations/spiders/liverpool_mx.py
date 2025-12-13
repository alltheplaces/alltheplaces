import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class LiverpoolMXSpider(scrapy.Spider):
    name = "liverpool_mx"
    item_attributes = {"brand": "Liverpool", "brand_wikidata": "Q1143318"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    start_urls = ["https://www.liverpool.com.mx/tienda/browse/storelocator"]

    def parse(self, response):
        element = json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').extract_first())
        for data in element["props"]["pageProps"]["data"]["StoreDataContent"]["stores"]:
            yield scrapy.http.FormRequest(
                url="https://www.liverpool.com.mx/getstoredetails",
                method="POST",
                body='{"storeId":"' + data["storeId"] + '"}',
                callback=self.store_data,
                cb_kwargs=dict(store=data),
            )

    def store_data(self, response, store):
        element = response.json()["storeDetails"]
        location = element["StoreDetails"]["1"]
        address = re.sub(r"(?si)Tel:.+|Teléfono.*|Tel\s*\..*", "", location["generalDetails"])
        address = re.sub(r"(?si)\n|\s{2,}|<.*?>", " ", address)
        item = DictParser.parse(store)
        item["branch"] = item.pop("name").replace("Liverpool ", "")
        item["addr_full"] = address
        item["phone"] = location["phone"]
        item["lat"] = store["lpLatitude"]
        item["lon"] = store["lpLongitude"]
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
