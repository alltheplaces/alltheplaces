import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import postal_regions


class KiaUSSpider(scrapy.Spider):
    name = "kia_us"
    item_attributes = {"brand": "Kia", "brand_wikidata": "Q35349"}

    def start_requests(self):
        for index, record in enumerate(postal_regions("US")):
            if index % 140 == 0:
                yield JsonRequest(
                    url="https://www.kia.com/us/services/en/dealers/search",
                    data={"type": "zip", "zipCode": record["postal_region"]},
                    headers={"Referer": "https://www.kia.com/us/en/find-a-dealer/"},
                )

    def parse(self, response, **kwargs):
        for dealer in response.json():
            dealer.update(dealer.pop("location"))
            item = DictParser.parse(dealer)
            item["ref"] = dealer.get("code")
            item["street_address"] = dealer.get("street1")
            if phones := dealer.get("phones"):
                item["phone"] = phones[0].get("number")
            item["website"] = f'https://www.kia.com/us/en/find-a-dealer/result?zipCode={dealer["zipCode"]}'
            item["extras"] = {"website_2": dealer.get("url")}
            item["extras"]["service"] = "dealer;repair"
            yield item
