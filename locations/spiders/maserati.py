import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MaseratiSpider(scrapy.Spider):
    name = "maserati"
    item_attributes = {
        "brand": "Maserati",
        "brand_wikidata": "Q35962",
    }
    allowed_domains = ["maserati.com"]
    start_urls = [
        "https://api.onthemap.io/server/v1/api/location?query=([sales]=[true] OR [assistance]=[true])&language=en&key=6e0b94fb-7f95-11ec-9c36-eb25f50f4870&channel=www.maserati.com",
    ]

    def parse(self, response):
        for row in response.json().get("data", {}).get("results", {}).get("features"):
            row.update(row.pop("properties"))
            item = DictParser.parse(row)
            item["ref"] = row.get("otm_id")
            item["street_address"] = item.pop("addr_full")
            item["country"] = row["countryIsoCode2"]
            item["email"] = row["emailAddr"]
            item["name"] = row["dealername"]
            apply_category(Categories.SHOP_CAR, item)
            yield item
