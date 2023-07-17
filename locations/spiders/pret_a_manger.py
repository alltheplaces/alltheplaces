import scrapy
from locations.storefinders.uberall import UberallSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]


class PretAMangerSpider(UberallSpider):
    name = "pret_a_manger"
    item_attributes = {
        "brand": "Pret A Manger",
        "brand_wikidata": "Q2109109",
    }
    veggie_pret = {"brand": "Veggie Pret", "brand_wikidata": "Q108118332"}
    key = "JOWxbXjWIu1zWqNZM8k56PggggAdY6"
    #
    # def parse_item(self, item, feature, **kwargs):
    #     if feature.get("storeType") == "veggie-pret":
    #         item["brand"] = self.veggie_pret["brand"]
    #         item["brand_wikidata"] = self.veggie_pret["brand_wikidata"]
    #     yield item

# class PretAMangerSpider(scrapy.Spider):
#     name = "pret_a_manger"
#     veggie_pret = {"brand": "Veggie Pret", "brand_wikidata": "Q108118332"}
#     item_attributes = {"brand": "Pret A Manger", "brand_wikidata": "Q2109109"}
#     start_urls = ["https://api1.pret.com/v1/shops"]
#
#     def parse(self, response):
#         for store in response.json()["shops"]:
#             if not store["active"]:
#                 continue
#
#             item = DictParser.parse(store)
#
#             if item["ref"] != "10414":
#                 continue
# `
#             item["street_address"] = ", ".join(filter(None, [item["housenumber"], item["street"]]))
#             item["housenumber"] = item["street"] = None
#
#             print(item)
#
#             oh = OpeningHours()
#             for i in range(0, 7):
#                 rule = store["tradingHours"][i]
#                 if rule:
#                     if rule in (["00:00", "00:00"], ["0:00AM", "0:00AM"], ["", ""]):
#                         continue
#
#                     if len(rule) != 2:
#                         continue
#
#                     if rule[0].startswith("0:"):
#                         rule[0] = rule[0].replace("0:", "12:", 1)
#                     if rule[1].startswith("0:"):
#                         rule[1] = rule[1].replace("0:", "12:", 1)
#
#                     oh.add_range(DAYS[i], rule[0], rule[1], "%I:%M%p")
#
#             item["opening_hours"] = oh.as_opening_hours()
#
#             item["extras"] = {}
#
#             item["extras"]["delivery"] = "yes" if store["features"]["delivery"] else "no"
#             item["extras"]["storeType"] = store["features"].get("storeType")
#             item["extras"]["wheelchair"] = "yes" if store["features"]["wheelchairAccess"] else "no"
#             item["extras"]["internet_access"] = "wlan" if store["features"]["wifi"] else "no"
#
#             if store["features"].get("storeType") == "veggie-pret":
#                 item["brand"] = self.veggie_pret["brand"]
#                 item["brand_wikidata"] = self.veggie_pret["brand_wikidata"]
#
#             yield item
