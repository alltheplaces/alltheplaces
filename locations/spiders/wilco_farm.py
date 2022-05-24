import json
import re
import scrapy
from locations.items import GeojsonPointItem


class WilcoFarmSpider(scrapy.Spider):
    name = "wilcofarm"
    item_attributes = {"brand": "Wilco Farm", "brand_wikidata": "Q8000290"}
    allowed_domains = ["www.farmstore.com"]

    start_urls = ("https://www.farmstore.com/locations/",)

    def parse(self, response):
        pattern = r"(var markers=\[)(.*?)(\]\;)"
        data = re.search(pattern, response.text, re.MULTILINE).group(2)
        data = json.loads("[" + data + "]")
        for item in data:
            properties = {
                "ref": item["storeId"],
                "name": item["storeName"],
                "addr_full": item["storeStreet"],
                "city": item["storeCity"],
                "state": item["storeState"],
                "postcode": item["storeZip"],
                "lat": item["storeLat"],
                "lon": item["storeLng"],
                "phone": item["storePhone"],
                "opening_hours": item["storeHours"],
            }

            yield GeojsonPointItem(**properties)
