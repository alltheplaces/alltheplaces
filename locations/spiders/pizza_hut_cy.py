import json
import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class PizzaHutCYSpider(scrapy.Spider):
    name = "pizza_hut_cy"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://www.pizzahut.com.cy/?api=phc&method=getDistricts"]

    def parse(self, response, **kwargs):
        for district in response.json()["data"]:
            yield JsonRequest(
                url=f"https://www.pizzahut.com.cy/?api=phc&method=getShopsByDistrictId&districtId={district['cityid']}",
                callback=self.parse_stores,
                cb_kwargs=dict(city=district["cityname"]),
            )

    def parse_stores(self, response, city):
        for store in response.json().get("data"):
            item = DictParser.parse(store)
            item["ref"] = store.get("lid")
            item["lat"], item["lon"] = store.get("coordinates").split(",")
            item["city"] = city
            details = json.loads(store.get("otherSettings"))
            item["addr_full"] = details.get("address").get("address_en")

            slug = "dinein"
            if services := details.get("store_services"):
                slug = "dinein" if services["dinein"] else "delivery"
                apply_yes_no(Extras.TAKEAWAY, item, services["take_away"])
                apply_yes_no(Extras.DELIVERY, item, services["delivery"])
                apply_yes_no(Extras.INDOOR_SEATING, item, services["dinein"])
                apply_yes_no(Extras.OUTDOOR_SEATING, item, services["outdoor_seating"])
                apply_yes_no(Extras.WIFI, item, services["wi_fi"])

            item["website"] = f'https://www.pizzahut.com.cy/restaurant/{slug}/{item["name"].lower().replace(" ", "-")}'
            apply_category(Categories.RESTAURANT, item)
            yield scrapy.Request(url=item["website"], callback=self.parse_opening_hours, cb_kwargs=dict(item=item))

    def parse_opening_hours(self, response, item):
        item["opening_hours"] = OpeningHours()
        if timing := response.xpath('//*[@id="ohours"]/following::div//tbody').get():
            for day, open_time, close_time in re.findall(r">\s*(\w+).+?(\d+:\d+)\s*-\s*(\d+:\d+)", timing, re.DOTALL):
                if day := sanitise_day(day):
                    item["opening_hours"].add_range(day, open_time, close_time)
        yield item
