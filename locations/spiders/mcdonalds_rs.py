import json
import re
import scrapy
from scrapy.selector import Selector
from locations.items import GeojsonPointItem


class McDonaldsRSSpider(scrapy.Spider):
    name = "mcdonalds_rs"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.rs"]

    start_urls = ("http://www.mcdonalds.rs/restoran-lokator/",)

    def normalize_item(self, data):
        match = re.sub("<[^<]+?>", "", data)
        return " ".join(match.split())

    def parse_postalCity(self, data):
        match = re.search(r"(.*\d)(.*\w)", data[1])
        if not match:
            return "", ""
        postalCode, city = match.groups()
        return self.normalize_item(postalCode), self.normalize_item(city)

    def parse_address(self, data):
        data = Selector(text=data).xpath("//p//text()").extract()
        address = self.normalize_item(data[0])
        postalCode, city = self.parse_postalCity(data)
        length = len(data)
        return address, postalCode, city

    def parse(self, response):
        try:
            match = re.search(r"var locations = (.*)</script>", response.text)
            data = json.loads(match.groups()[0])
        except ValueError:
            return

        for item in data:
            address, postalCode, city = self.parse_address(item[3])
            properties = {
                "name": item[1],
                "website": item[2],
                "ref": item[0],
                "lon": item[4],
                "lat": item[5],
                "city": city,
                "addr_full": address,
                "postcode": postalCode,
            }

            yield GeojsonPointItem(**properties)
