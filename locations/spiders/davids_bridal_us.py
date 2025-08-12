from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class DavidsBridalUSSpider(Spider):
    name = "davids_bridal_us"
    item_attributes = {"brand": "David's Bridal", "brand_wikidata": "Q5230388"}
    allowed_domains = ["www.davidsbridal.com"]
    start_urls = ["https://www.davidsbridal.com/api/aem/locations"]

    def parse(self, response):
        locations = response.json().get("data", {}).get("locations", {}).get("edges", [])
        for raw_data in locations:
            data = raw_data.get("node", {})
            if not data or data.get("name") == "Shop location":
                continue
            data.update(data.pop("address", {}))
            item = DictParser.parse(data)
            item["ref"] = data.get("storeId", {}).get("value")
            item["branch"] = item.pop("name", None)
            item["addr_full"] = ", ".join(data.get("formatted", []))
            item["street_address"] = clean_address([data.get("address1"), data.get("address2")])
            item["website"] = (
                f"https://www.davidsbridal.com/stores/"
                f'{data.get("city", "").replace(" ", "").lower()}-'
                f'{data.get("provinceCode", "").lower()}-'
                f'{data.get("zip", "").replace("-", "")}-'
                f'{item["ref"]}?storeLocation=US'
            )

            yield item
