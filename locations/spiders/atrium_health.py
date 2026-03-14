from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.items import Feature


class AtriumHealthSpider(Spider):
    name = "atrium_health"
    item_attributes = {"operator": "Atrium Health", "operator_wikidata": "Q5044932"}
    allowed_domains = ["atriumhealth.org"]

    async def start(self) -> AsyncIterator[FormRequest]:
        base_url = "https://atriumhealth.org/mobileDataApI/MobileserviceAPi/LocationSearch?cityName=Charlotte%2C+NC+28202%2C+USA&locationType=&locationName=&pageNumber={page}&pageSize=793&latitude=35.2326781&longitude=-80.8460822&sortBy=Distance&datasource=f829e711-f2ef-4b46-98d6-a268f958a2d0&childrensLocationOnly=false&community=All+Communities"

        headers = {
            "request-context": "appId=cid-v1:a0e1891c-1d13-4f2a-8949-dded6b098266",
            "request-id": "|7RH8Z.icrhs",
            "accept-encoding": "gzip, deflate, br",
            "accept": "application/json",
            "sec-ch-ua": '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
            "sec-fetch-site": "same-origin",
            "referer": "https://atriumhealth.org/locations?cityName=Charlotte_NC_28202_USA&locationType=&locationName=&pageNumber=1&pageSize=5&latitude=35.2326781&longitude=-80.8460822&sortBy=Distance&datasource=f829e711-f2ef-4b46-98d6-a268f958a2d0&childrensLocationOnly=false&community=All_Communities",
        }

        for page in range(1, 160):
            url = base_url.format(page=page)

            yield FormRequest(url=url, method="GET", headers=headers, callback=self.parse)

    def parse(self, response):
        data = response.json()

        for place in data["Locations"]:
            properties = {
                "ref": place["ItemId"],
                "name": place["Name"],
                "street_address": place["Address"],
                "city": place["City"],
                "state": place["State"],
                "postcode": place["PostalCode"],
                "lat": place["Latitude"],
                "lon": place["Longitude"],
                "phone": place["Phone"],
                "website": "https://atriumhealth.org" + place["ClickableUri"],
            }

            yield Feature(**properties)
