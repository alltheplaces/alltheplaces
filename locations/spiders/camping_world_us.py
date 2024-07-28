import json
from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest, Request

from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CampingWorldUSSpider(scrapy.Spider):
    name = "camping_world_us"
    item_attributes = {"brand": "Camping World", "brand_wikidata": "Q5028383"}

    locator_url = "https://rv.campingworld.com/state-directory"
    api_url = "https://api.rvs.com/api/geodata/getclosestdealer"
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    request_json = """
        {
            "zipCode":"66952",
            "domainId":1,
            "take":2000,
            "hours":true,
            "facilities":true,
            "requirements":{},
            "glCodes":"",
            "standAlone":true
        }
    """.strip()

    def start_requests(self):
        yield Request(url=self.locator_url, callback=self.parse_locator)

    def parse_locator(self, response):
        # The locator HTML contains a JWT in a meta tag that we need to make the API call.
        token = response.xpath('//meta[starts-with(@content, "eyJ")][contains(@content, ".eyJ")]/@content').get()

        if token is None:
            raise Exception("No token found in locator HTML")

        yield JsonRequest(
            url=self.api_url,
            method="POST",
            body=self.request_json,
            headers={"x-auth-token": token},
            callback=self.parse,
        )

    def parse(self, response):
        for store in json.loads(response.xpath("/html/body/pre/text()").get())["closestDealer"]:
            yield Feature(
                lat=store["lat"],
                lon=store["long"],
                name=store["marketing_name__c"],
                ref=store["location_id__c"],
                addr_full=f"{store['billingstreet']} {store['billingcity']}, {store['billingstatecode']} {store['billingpostalcode']}",
                street_address=store["billingstreet"],
                postcode=store["billingpostalcode"],
                city=store["billingcity"],
                state=store["billingstatecode"],
                country="US",
                phone=store["phone"],
                website=urljoin("https://rv.campingworld.com/dealer/", store["dealer_url"]),
            )
