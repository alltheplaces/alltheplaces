import base64
import json

import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class RalphLaurenSpider(scrapy.Spider):
    name = "ralph_lauren"
    item_attributes = {"brand_wikidata": "Q1641437"}
    start_urls = ["https://www.ralphlauren.com/stores"]
    custom_settings = {"COOKIES_ENABLED": False, "ROBOTSTXT_OBEY": False}
    download_delay = 10
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse(self, response, **kwargs):
        for country in filter(
            None, response.xpath('//select[@id="dwfrm_storelocator_country"]/option/@value').getall()
        ):
            yield response.follow(
                url=f"/findstores?dwfrm_storelocator_country={country}&dwfrm_storelocator_findbycountry=Search&findByValue=CountrySearch",
                callback=self.parse_country,
            )

    def parse_country(self, response, **kwargs):
        store_data = response.xpath("//@data-storejson").get()
        if not store_data:
            return
        for location in json.loads(store_data):
            location["name"] = base64.b64decode(location["name"]).decode("utf-8")
            location["street_address"] = base64.b64decode(location.pop("address1")).decode("utf-8")
            location["website"] = response.urljoin("/Stores-Details?StoreID={}".format(location["id"]))

            yield DictParser.parse(location)
