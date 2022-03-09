import json
import scrapy

from locations.items import GeojsonPointItem


class BuildersFirstSourceSpider(scrapy.Spider):
    name = "builders_firstsource"
    item_attributes = {"brand": "Builders FirstSource"}
    allowed_domains = ["bldr-back-central.azurewebsites.net"]

    def start_requests(self):
        url = "https://bldr-back-central.azurewebsites.net/umbraco/api/LocationData/GetAllLocations"

        payload = '{radius: 150, DistributionList: "", installedServiceName: ""}\n'
        # {"radius":150,"DistributionList":"","installedServiceName":""}
        headers = {
            "Content-Type": "application/json",
            "Cookie": "ARRAffinity=2192faf4b84e1a2cbe60224d6bf89c9f255ed7b693d5e04a43de12ab1a54868a; ARRAffinitySameSite=2192faf4b84e1a2cbe60224d6bf89c9f255ed7b693d5e04a43de12ab1a54868a",
        }

        yield scrapy.Request(
            url=url, callback=self.parse, method="POST", headers=headers, body=payload
        )

    def parse(self, response):
        jsonData = json.loads(response.text)
        for i in jsonData:
            properties = {
                "name": i["Name"],
                "ref": i["Id"],
                "addr_full": i["Address1"] + " " + i["Address2"],
                "city": i["City"],
                "state": i["State"],
                "postcode": i["ZipCode"],
                "country": "US",
                "phone": i["PhoneNo"],
                "lat": i["Latitude"],
                "lon": i["Longitude"],
            }
            yield GeojsonPointItem(**properties)
