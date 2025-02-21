import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class SsangyongDESpider(scrapy.Spider):
    name = "ssangyong_de"
    item_attributes = {"brand": "SsangYong", "brand_wikidata": "Q221869"}
    start_urls = [
        "https://www.ssangyong.de/haendler",
    ]
    no_refs = True

    def parse(self, response, **kwargs):
        item = Feature()
        data = response.xpath('//script[contains(text(), "var marker")]/text()').get()
        pattern = re.compile(r"maps\.LatLng(.+?);var marker", re.DOTALL)
        for shop in re.findall(pattern, data):
            item["lat"], item["lon"] = re.search(r"\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)", shop).groups()
            item["name"] = re.search(r"locname\">(.*?)<", shop).group(1)
            if phone := re.search(r"Telefon:\s*([0-9\-]+)", shop):
                item["phone"] = phone.group(1)
            item["addr_full"] = re.search(r"nazwa\"></span>(.*)<br/><span", shop).group(1).replace("<br/>", ", ")
            item["website"] = re.search(r"floatNone\">(.*?)\s*</a>", shop).group(1)
            apply_category(Categories.SHOP_CAR, item)
            if "service" in item["name"].lower():
                item["extras"]["service"] = True
            yield item
