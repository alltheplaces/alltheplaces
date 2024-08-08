from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class BrookdaleUSSpider(Spider):
    name = "brookdale_us"
    item_attributes = {"brand": "Brookdale", "brand_wikidata": "Q4974387"}
    allowed_domains = ["www.brookdale.com"]
    start_urls = [
        "https://www.brookdale.com/bin/brookdale/search/global?fq=(contentCategory%3Alocations)&bq=(contentType%3Acommunity^0.025)&pt=43.0389025%2C-87.9064736&d=100000&rows=10000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["community_id"].replace("BUS-", "")
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["postcode"] = location["zip_postal_code"]
            item["phone"] = location["phone_main"]
            item["email"] = location["community_contact_email"]
            yield item
