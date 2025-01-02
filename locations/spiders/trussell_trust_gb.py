import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class TrussellTrustGBSpider(Spider):
    name = "trussell_trust_gb"
    item_attributes = {"operator_wikidata": "Q15621299"}
    start_urls = ["https://www.trussell.org.uk/emergency-food/i-have-a-food-voucher/choose-a-foodbank?lat=&lng=&page=1"]

    def make_request(self, page: int):
        return scrapy.Request(
            url="https://www.trussell.org.uk/emergency-food/i-have-a-food-voucher/choose-a-foodbank?lat=&lng=&page={}".format(
                page
            ),
            cb_kwargs={"page": page},
        )

    def start_requests(self):
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := response.xpath('//script[contains(text(),"markers")]/text()').get():
            raw_data = data.replace("\\", "").replace("groupT itle", "groupTitle").replace("p ostcode", "postcode")
            pattern = re.compile(
                r"\"groupTitle\":\"([^\"]+)\".*?\"domain\":\"([^\"]+)\".*?\"title\":\"([^\"]+)\".*?\"address01\":\"([^\"]+)\".*?\"address02\":\"?(null|[^\"]+)\"?.*?\"county\":\"?(null|[^\"]+)\"?.*?\"town\":\"?(null|[^\"]+)\"?.*?\"postcode\":\"(null|[^\"]+)\".*?\"email\":\"([^\"]+)\".*?\"telephone\":\"([^\"]+)\".*?\"uuid\":\"([^\"]+)\".*?\"coordinates\":\[\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)\s*\]"
            )
            for food_bank in re.findall(pattern, raw_data):
                item = Feature()
                item["name"] = food_bank[0]
                item["website"] = "https://" + food_bank[1]
                item["branch"] = food_bank[2]
                item["postcode"] = food_bank[7]
                item["email"] = food_bank[8]
                item["phone"] = food_bank[9]
                item["ref"] = food_bank[10]
                item["lat"] = food_bank[-2]
                item["lon"] = food_bank[-1]
                item["street"] = food_bank[3]
                if food_bank[5] != "null":
                    item["state"] = food_bank[5]
                if food_bank[6] != "null":
                    item["city"] = food_bank[6]
                if food_bank[4] != "null":
                    item["street_address"] = ",".join([food_bank[3], food_bank[4]])
                yield item
            next_page = kwargs["page"] + 1
            yield self.make_request(next_page)
