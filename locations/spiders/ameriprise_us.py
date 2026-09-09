import json
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AmeripriseUSSpider(Spider):
    name = "ameriprise_us"
    item_attributes = {"brand": "Ameriprise Financial", "brand_wikidata": "Q2843129"}
    start_urls = ["https://www.ameripriseadvisors.com/find-a-financial-advisor-by-state/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state in response.xpath('//*[@class="public-sitemap-list"]//a/text()').getall():
            yield scrapy.Request(url=response.urljoin(state), callback=self.parse_city, cb_kwargs={"state": state})

    def parse_city(self, response: Response, state: str) -> Any:
        for city in response.xpath('//*[@class="public-sitemap-list"]//a/text()').getall():
            payload = {"searchTerm": f"{city}, {state}", "numberOfRowsToReturn": "50", "searchType": "city, state"}
            yield JsonRequest(
                url="https://www.ameripriseadvisors.com/api/locatorsearch/search/",
                data={"criteria": json.dumps(payload)},
                callback=self.parse_details,
            )

    def parse_details(self, response: Response) -> Any:
        for advisor in response.json().get("locatorResultModels", []):
            for location in advisor.get("locations", []):
                item = DictParser.parse(location)
                item.pop("name")
                item["ref"] = item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
                apply_category(Categories.OFFICE_FINANCIAL_ADVISOR, item)
                yield item
