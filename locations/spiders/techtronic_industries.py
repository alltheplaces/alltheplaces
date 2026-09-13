from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TechtronicIndustriesSpider(Spider):
    name = "techtronic_industries"
    item_attributes = {"brand": "Techtronic Industries", "brand_wikidata": "Q2399612"}
    start_urls = ["https://www.ttigroup.com/ttigroup/api/v1/node/office?lang=en&page_nid=1161"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for office in response.json():
            address = office.get("office_address") or {}

            item = Feature()
            item["ref"] = item["name"] = office.get("office_title")
            item["lat"] = office.get("office_latitude")
            item["lon"] = office.get("office_longitude")

            item["addr_full"] = " ".join((office.get("office_address_text") or "").split())
            item["country"] = address.get("country_code")
            item["state"] = address.get("administrative_area")
            if postcode := address.get("postal_code"):
                if postcode != "000000":
                    item["postcode"] = postcode

            if numbers := office.get("office_contact_numbers"):
                item["phone"] = "; ".join(numbers)

            if links := office.get("office_contact_links"):
                item["website"] = links[0].get("uri")

            apply_category(Categories.OFFICE_COMPANY, item)

            yield item
