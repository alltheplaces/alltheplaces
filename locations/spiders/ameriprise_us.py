import json

import scrapy
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AmeripriseUSSpider(Spider):
    name = "ameriprise_us"
    item_attributes = {"brand": "Ameriprise Financial", "brand_wikidata": "Q2843129"}
    start_urls = ["https://www.ameripriseadvisors.com/find-a-financial-advisor-by-state/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        # Extract list of states
        state_list = response.xpath('//*[@class="public-sitemap-list"]//a/text()').getall()
        for state in state_list:
            state_url = response.urljoin(state)
            yield scrapy.Request(url=state_url, callback=self.parse_city, cb_kwargs={"state": state})

    def parse_city(self, response, state):
        # Extract list of cities for the given state
        city_list = response.xpath('//*[@class="public-sitemap-list"]//a/text()').getall()
        for city in city_list:
            payload = {"searchTerm": f"{city}, {state}", "numberOfRowsToReturn": "50", "searchType": "city, state"}
            yield scrapy.FormRequest(
                url="https://www.ameripriseadvisors.com/webservices/advisorSearch.aspx",
                formdata={"criteria": json.dumps(payload)},
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST",
                callback=self.parse_details,
            )

    def parse_details(self, response):
        for advisor in response.json().get("locatorResultModels", []):
            for location in advisor.get("locations", []):
                item = DictParser.parse(location)
                item.pop("name")
                item["ref"] = item["addr_full"] = merge_address_lines([location["address1"], location["address2"]])
                yield item
