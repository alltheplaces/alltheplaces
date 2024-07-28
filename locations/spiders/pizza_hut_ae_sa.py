import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaHutAESASpider(scrapy.Spider):
    name = "pizza_hut_ae_sa"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for key, value in {"uae": "uae", "saudi": "ksa"}.items():
            body = f'{{"payload":{{"path":"https://phprodblob-a0gebddqcze0bwhz.a03.azurefd.net/phprodblobstorage/phd/production/","country":"{value}","subPath":"?sv=2020-02-10&ss=bf&srt=o&sp=rlf&se=2025-06-21T02:09:06Z&st=2021-06-20T18:09:06Z&spr=https&sig=1jVlax0%2FNb2czQlUGw6kZv5KEvtVHSu4T7F0s0%2Fefyw%3D"}}}}'
            headers = {"Content-Type": "application/json", "brand": "PHD"}
            url = f"https://{key}.pizzahut.me/api/getStoreList"
            yield scrapy.Request(
                url=url, method="POST", body=body, headers=headers, callback=self.parse, cb_kwargs={"country": key}
            )

    def parse(self, response, **kwargs):
        for data in response.json():
            for store in data["store"]:
                item = DictParser.parse(store)
                item["name"] = store.get("name_en")
                item["addr_full"] = store.get("address_en")
                item["street_address"] = store.get("areaName")
                item["phone"] = store.get("phone1")
                item["website"] = f"https://{kwargs['country']}.pizzahut.me/"
                if kwargs["country"] == "uae":
                    item["country"] = "AE"
                elif kwargs["country"] == "saudi":
                    item["country"] = "SA"
                apply_category(Categories.RESTAURANT, item)
                yield item
