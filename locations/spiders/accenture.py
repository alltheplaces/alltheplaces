import html
import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AccentureSpider(Spider):
    name = "accenture"
    item_attributes = {"brand": "Accenture", "brand_wikidata": "Q338825"}
    start_urls = ["https://www.accenture.com/us-en/about/location"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for country in response.xpath('//a[contains(@class, "rad-office-location-country__link")]//text()').getall():
            yield JsonRequest(
                url=f"https://www.accenture.com/us-en/about/locations/office-details/jcr:content/root/container_main/locationhero_copy.result.html?query={country}&from=0&size=1500",
                callback=self.parse_office,
            )

    def parse_office(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for office in json.loads(html.unescape(response.text)):
            item = DictParser.parse(office)
            item.pop("state")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["postcode"] = office.get("postalZipCode", "")
            item["phone"] = office.get("contactTel", "")
            apply_category(Categories.OFFICE_CONSULTING, item)

            yield item
