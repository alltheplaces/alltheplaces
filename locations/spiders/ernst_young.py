from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class ErnstYoungSpider(scrapy.Spider):
    name = "ernst_young"
    item_attributes = {"brand": "EY", "brand_wikidata": "Q489097"}
    start_urls = ["https://www.ey.com/content/ey-unified-site/ey-com.office-locations.json?site=ey-com&locale=en_us"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for country in data["countries"]:
            for cities in country["cities"]:
                for office in cities["offices"]:
                    yield self.parse_office(office)
            for state in country["states"]:
                for cities in state["cities"]:
                    for office in cities["offices"]:
                        yield self.parse_office(office)

    def parse_office(self, office: dict) -> Feature:
        item = Feature()
        item["name"] = office["officeName"]
        item["postcode"] = office["officePostalCode"]
        item["lat"] = office["officeMapLatitude"]
        item["lon"] = office["officeMapLongitude"]
        item["city"] = office["cityName"]
        item["street_address"] = clean_address(office["officeAddress"].replace("<p>", "").replace("</p>", ""))
        if phone := office.get("phoneInformationDirect"):
            item["phone"] = phone[0]
        item["state"] = office["stateName"]
        item["ref"] = item["website"] = urljoin("https://www.ey.com", office["href"])
        return item
