import scrapy
import re
import json
import lxml
from locations.items import GeojsonPointItem


class ChromeIndustriesSpider(scrapy.Spider):
    name = "chrome_industries"
    item_attributes = {"brand": "Chrome Industries"}
    allowed_domains = ["www.chromeindustries.com"]
    start_urls = (
        "https://www.chromeindustries.com/on/demandware.store/Sites-chrome_na-Site/en_US/Stores-Search?latitude=32.7269669&longitude=-117.16470939999999&maxDistance=50000000",
    )

    def parse(self, response):
        json_data = json.loads(response.text.replace("null", '""'))
        for item in json_data["locations"]:
            properties = {
                "addr_full": item["address"] + " " + item["address2"],
                "phone": item["phone"],
                "name": item["name"],
                "city": item["city"],
                "state": item["state"],
                "postcode": item["zipcode"],
                "ref": item["id"],
                "website": "https://www.chromeindustries.com/stores/",
                "lat": float(item["latitude"]),
                "lon": float(item["longitude"]),
            }
            yield GeojsonPointItem(**properties)
