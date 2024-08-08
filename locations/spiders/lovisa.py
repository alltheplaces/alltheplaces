from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class LovisaSpider(Spider):
    name = "lovisa"
    item_attributes = {"brand": "Lovisa", "brand_wikidata": "Q106298409"}
    allowed_domains = ["lovisa-stores.herokuapp.com"]
    start_urls = ["https://lovisa-stores.herokuapp.com/all-stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # HTTP 500 error for robots.txt

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = str(location.get("branch", location.get("_id")))
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item.pop("website")  # websites are generally just malls, not individual stores within
            yield item
