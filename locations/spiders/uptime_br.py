import json

from scrapy import FormRequest, Selector, Spider

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.google_url import extract_google_position


class UptimeBRSpider(Spider):
    name = "uptime_br"
    item_attributes = {"brand": "UPTIME", "brand_wikidata": "Q123564373"}
    start_urls = ["https://uptime.com.br/unidades-uptime"]

    def parse(self, response, **kwargs):
        token = response.xpath('//input[@name="_token"]/@value').get()
        for state in response.xpath('//optgroup[@label="states"]/option/@value').getall():
            yield FormRequest(
                url="https://uptime.com.br/ajax_cities",
                formdata={"_token": token, "state": state},
                callback=self.parse_cities,
                cb_kwargs={"token": token},
            )

    def parse_cities(self, response, token, **kwargs):
        for city in response.json()["cities"]:
            yield FormRequest(
                url="https://uptime.com.br/ajax_branches",
                formdata={"_token": token, "cities": city["city"]},
                callback=self.parse_branches,
                cb_kwargs={"token": token},
            )

    def parse_branches(self, response, token, **kwargs):
        for branch in response.json()["branches"]:
            yield FormRequest(
                url="https://uptime.com.br/ajax_show_branch",
                formdata={"_token": token, "branches": branch["id"]},
                callback=self.parse_branch_details,
            )

    def parse_branch_details(self, response, **kwargs):
        branch = json.loads(response.json()["script"].replace("show_branch", "").strip("()"))
        item = DictParser.parse(branch)
        item["branch"] = item.pop("name").replace("UNIDADE ", "")
        item["street_address"] = item.pop("addr_full")
        item["phone"] = "; ".join(filter(None, [branch.get("phone1"), branch.get("phone2")]))
        extract_google_position(item, Selector(text=branch["map"]))
        apply_category({"amenity": "language_school"}, item)
        yield item
