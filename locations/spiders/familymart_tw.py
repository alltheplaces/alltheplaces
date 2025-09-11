from typing import Any

from chompjs import parse_js_object
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FamilymartTWSpider(Spider):
    name = "familymart_tw"
    item_attributes = {"brand_wikidata": "Q10891564"}
    allowed_domains = ["www.family.com.tw", "api.map.com.tw"]
    start_urls = ["https://www.family.com.tw/Marketing/storemap/?v=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for admin_area_onclick in response.xpath('//a[contains(@onclick, "showAdminArea(")]/@onclick').getall():
            admin_area = admin_area_onclick.split("'", 2)[1]
            yield Request(
                url=f"https://api.map.com.tw/net/familyShop.aspx?searchType=ShowTownList&type=&city={admin_area}&fun=storeTownList&key=6F30E8BF706D653965BDE302661D1241F8BE9EBC",
                headers={"Referer": "https://www.family.com.tw/"},
                callback=self.parse_town_list,
            )

    def parse_town_list(self, response):
        for town_data in parse_js_object(response.text):
            admin_area = town_data["city"]
            town = town_data["town"]
            yield Request(
                url=f"https://api.map.com.tw/net/familyShop.aspx?searchType=ShopList&type=&city={admin_area}&area={town}&road=&fun=showStoreList&key=6F30E8BF706D653965BDE302661D1241F8BE9EBC",
                meta={"state": admin_area, "city": town},
                headers={"Referer": "https://www.family.com.tw/"},
                callback=self.parse_store_list,
            )

    def parse_store_list(self, response):
        for location in parse_js_object(response.text):
            item = DictParser.parse(location)
            item["ref"] = location["pkey"]
            item["lat"] = location["py"]
            item["lon"] = location["px"]
            item["street"] = location["road"]
            item["city"] = response.meta["city"]
            item["state"] = response.meta["state"]
            item["postcode"] = location["post"]

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
