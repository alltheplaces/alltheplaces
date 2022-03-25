# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ColdstoneCreamerySpider(scrapy.Spider):
    name = "coldstone_creamery"
    item_attributes = {"brand": "Coldstone Creamery"}
    allowed_domains = ["www.coldstonecreamery.com"]
    start_urls = (
        "https://www.coldstonecreamery.com/locator/index.php?brand=14&mode=desktop&pagesize=7000&q=55114",
    )

    def parse(self, response):
        for location_node in response.xpath('//div[@class="listing"]/script/text()'):
            location_js = location_node.extract()
            first_bracket = location_js.find("{")
            last_bracket = location_js.rfind("}")
            store_obj = json.loads(location_js[first_bracket : last_bracket + 1])

            props = {
                "addr_full": store_obj["Address"],
                "city": store_obj["City"],
                "state": store_obj["State"],
                "postcode": store_obj["Zip"],
                "country": store_obj["CountryCode"],
                "phone": store_obj["Phone"],
                "ref": store_obj["StoreId"],
                "website": response.urljoin("/stores/%s" % store_obj["StoreId"]),
                "lat": store_obj["Latitude"],
                "lon": store_obj["Longitude"],
            }

            yield GeojsonPointItem(**props)
