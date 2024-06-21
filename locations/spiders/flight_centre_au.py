import base64
import json

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class FlightCentreAUSpider(Spider):
    name = "flight_centre_au"
    item_attributes = {"brand": "Flight Centre", "brand_wikidata": "Q5459202"}
    allowed_domains = ["www.flightcentre.com.au", "aws.found.io"]
    start_urls = ["https://www.flightcentre.com.au/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.request_stores)

    def request_stores(self, response):
        # The store locator page has a JSON object containing details of the API endpoint to connect to
        nextdata = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        api_host = nextdata["props"]["pageProps"]["config"]["data"]["stores"]["host"]
        api_env = nextdata["props"]["pageProps"]["config"]["data"]["stores"]["index"]
        api_url = f"{api_host}/{api_env}/_msearch"
        api_user = nextdata["props"]["pageProps"]["config"]["data"]["stores"]["username"]
        api_pass = nextdata["props"]["pageProps"]["config"]["data"]["stores"]["password"]
        api_token = f"{api_user}:{api_pass}"
        query = {
            "query": {"match_all": {}},
            "size": 10000,
            "_source": {
                "includes": [
                    "name",
                    "slug",
                    "address1",
                    "address2",
                    "address3",
                    "locality",
                    "state",
                    "opening_hours",
                    "toll_free_number__tel",
                    "geo_location",
                ],
                "excludes": [],
            },
            "from": 0,
            "sort": [],
        }
        body = '{"preference":"StoreController"}\n' + json.dumps(query) + "\n"
        headers = {
            "Authorization": "Basic " + base64.b64encode(api_token.encode("ascii")).decode("ascii"),
            "Content-Type": "application/x-ndjson",
        }
        yield Request(url=api_url, method="POST", headers=headers, body=body)

    def parse(self, response):
        for location in response.json()["responses"][0]["hits"]["hits"]:
            if "Flight Centre" not in location["_source"]["name"]:
                continue
            item = DictParser.parse(location["_source"])
            item["ref"] = location["_id"].split(":", 1)[0]
            item["street_address"] = clean_address(
                [
                    location["_source"].get("address1"),
                    location["_source"].get("address2"),
                    location["_source"].get("address3"),
                ]
            )
            item["phone"] = location["_source"].get("toll_free_number__tel")
            if location["_source"].get("slug"):
                item["website"] = "https://www.flightcentre.com.au/stores/" + location["_source"]["slug"]
            item["opening_hours"] = OpeningHours()
            for day in location["_source"]["opening_hours"]:
                if day["closed"]:
                    continue
                item["opening_hours"].add_range(day["day"], day["open"], day["close"])
            yield item
