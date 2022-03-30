import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsMYSpider(scrapy.Spider):
    name = "mcdonalds_my"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.com.my"]

    def start_requests(self):
        url = "https://www.mcdonalds.com.my/storefinder/index.php"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.mcdonalds.com.my",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Referer": "https://www.mcdonalds.com.my/locate-us",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        form_data = {
            "action": "get_nearby_stores",
            "distance": "100",
            "lat": "4.210484",
            "lng": "101.975766",
            "ajax": "1",
        }

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            formdata=form_data,
            headers=headers,
            callback=self.parse,
        )

    def parse_address(self, address):
        data = address.split(",")
        length = len(data)
        if length == 1:
            return address, "", "", ""
        state = data[length - 2].strip()
        city = data[length - 3].strip()
        postalCode = data[length - 4].strip()
        return address, city, state, postalCode

    def parse(self, response):
        stores = response.json()
        stores = stores["stores"]
        index = 0
        for item in stores:
            address, city, state, postalCode = self.parse_address(item["address"])
            properties = {
                "ref": index,
                "name": item["name"],
                "lat": item["lat"],
                "lon": item["lng"],
                "phone": item["telephone"],
                "opening_hours": "24/7",
                "addr_full": address,
                "city": city,
                "state": state,
                "postcode": postalCode,
            }

            index = index + 1

            yield GeojsonPointItem(**properties)
