import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class WeltladenATSpider(scrapy.Spider):
    name = "weltladen_at"
    item_attributes = {"brand": "Weltladen", "brand_wikidata": "Q1640782"}
    start_urls = ["https://www.weltladen.at/weltlaeden/weltladen-finden/"]
    no_refs = True

    def parse(self, response, **kwargs):
        data = response.xpath('//script[contains(text(), "var marker")]/text()').get()
        pattern = re.compile(r"var loc=new google.maps(.+?)div>';", re.DOTALL)

        for store in re.findall(pattern, data):
            item = Feature()
            item["branch"] = re.search(r"h2>(.*)</h2", store).group(1).replace(" Weltladen", "")
            item["addr_full"] = re.search(r"p>(.*)<br>Telefon", store).group(1)
            item["phone"] = re.search(r"Telefon:.*>(.*)</a><br>E-Mail", store).group(1)
            item["email"] = re.search(r"E-Mail:.*\">(.*)</a><br>", store).group(1)
            item["lat"], item["lon"] = re.search(r"LatLng\((-?\d+.\d+),(-?\d+.\d+)\)", store).groups()
            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
