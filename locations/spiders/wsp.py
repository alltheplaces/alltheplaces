import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class WspSpider(scrapy.Spider):
    name = "wsp"
    item_attributes = {"brand": "WSP", "brand_wikidata": "Q1333162"}
    allowed_domains = ["www.wsp.com"]
    start_urls = ("https://www.wsp.com/",)

    def parse(self, response):
        url = "https://www.wsp.com/api/sitecore/Maps/GetMapPoints"

        formdata = {
            "itemId": "{2F436202-D2B9-4F3D-8ECC-5E0BCA533888}",
        }

        yield scrapy.http.FormRequest(
            url,
            self.parse_store,
            method="POST",
            formdata=formdata,
        )

    def parse_store(self, response):
        office_data = json.loads(response.text)

        for office in office_data:
            try:
                properties = {
                    "ref": office["ID"]["Guid"],
                    "addr_full": office["Address"],
                    "lat": office["Location"].split(",")[0],
                    "lon": office["Location"].split(",")[1],
                    "name": office["Name"],
                    "website": response.urljoin(office["MapPointURL"]),
                }
            except IndexError:
                continue

            apply_category(Categories.OFFICE_ENGINEER, properties)

            yield Feature(**properties)
