import scrapy
from scrapy.http import JsonRequest
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VakifbankTRSpider(scrapy.Spider):
    name = "vakifbank_tr"
    item_attributes = {"brand": "Vakıfbank", "brand_wikidata": "Q1148521"}
    requires_proxy = "TR"

    def start_requests(self):
        yield scrapy.Request(
            url="https://apigw.vakifbank.com.tr:8443/auth/oauth/v2/token",
            body="client_id=l7xx672ef83670e842b0bb2f13a539ddbfb5&client_secret=282ce53197da4c0cb8f7bd658a14a6c3&grant_type=client_credentials&scope=public",
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            method="POST",
            callback=self.parse_token,
        )

    def parse_token(self, response):
        token = response.json()["access_token"]
        for branch_type in ["Branch", "ATM"]:
            url = f"https://apigw.vakifbank.com.tr:8443/vakifbank{branch_type}List"
            payload = {"Status": 1} if branch_type == "Branch" else {"CurrencyCode": "1"}
            yield JsonRequest(
                url=url,
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                cb_kwargs={"branch_type": branch_type},
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        data_key = "Branch" if kwargs["branch_type"] == "Branch" else "ATM"
        for item_data in response.json().get("Data").get(data_key):
            item = DictParser.parse(item_data)
            item["addr_full"] = item_data[f"{data_key}Address"]
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            if kwargs["branch_type"] == "ATM":
                item["ref"] = item_data["ATMCode"]
                item["lat"] = item_data["Latitude"].replace(",", ".")
                item["lon"] = item_data["Longitude"].replace(",", ".")
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
