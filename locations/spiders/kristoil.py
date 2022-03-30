import re
import scrapy
from locations.items import GeojsonPointItem


class KristoilSpider(scrapy.Spider):
    name = "kristoil"
    item_attributes = {"brand": "Kristoil"}
    allowed_domains = ["www.kristoil.com"]

    def start_requests(self):
        url = "http://www.kristoil.com/wp-content/themes/krist/ajax/map.php"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "http://www.kristoil.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "Referer": "http://www.kristoil.com/locations/",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }
        form_data = {}

        yield scrapy.http.FormRequest(
            url=url,
            method="GET",
            formdata=form_data,
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        phoneregex = re.compile(r"^<a.+>([0-9\-]+)<\/a>$")
        stores = response.json()
        for key, value in stores.items():
            all_address = value["address"].split(",")
            len_address = len(all_address)
            state_zipcode = all_address[len_address - 1]
            zipcode = re.findall(r"(\d{5})", state_zipcode)
            addr_full = re.findall(r"^[^(,|.)]+", value["address"])[0]
            if len(zipcode) > 0:
                zipcode = zipcode[0]
            else:
                zipcode = ""
            state = re.findall(r"([A-Z]{2})", state_zipcode)
            if len(state) > 0:
                state = state[0]
            else:
                state = ""
            properties = {
                "ref": value["ID"],
                "name": value["title"],
                "addr_full": addr_full,
                "city": value["title"],
                "state": state,
                "postcode": zipcode,
                "lat": value["location"]["lat"],
                "lon": value["location"]["lng"],
            }
            if value["phone"]:
                properties["phone"] = value["phone"]
            yield GeojsonPointItem(**properties)
