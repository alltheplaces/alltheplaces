import re

import scrapy
from chompjs import chompjs

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class BnpParibasFortisBESpider(scrapy.Spider):
    name = "bnp_paribas_fortis_be"
    item_attributes = {"brand": "BNP Paribas Fortis", "brand_wikidata": "Q796827"}
    start_urls = ["https://branch.bnpparibasfortis.be/engineV2/?enc=json&crit=agence&ag=allpoi"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "COOKIES_ENABLED": False}
    headers = {
        "Referer": "https://branch.bnpparibasfortis.be/m/nl/?crit=branch",
        "Cookie": "PHPSESSID=0rhuli6ja9kfdsto74ckamvrdj",
    }

    def parse(self, response, **kwargs):
        result = chompjs.parse_js_object(response.text).get("agence")
        for location in result:
            lat = location["lat"]
            lon = location["lng"]
            url = f"https://branch.bnpparibasfortis.be/engineV2/?crit=agence&geoLatLng={lat}%2C{lon}"
            yield scrapy.Request(url=url.replace('"', ""), callback=self.parse_details)

    def parse_details(self, response):
        for store in response.json()["agence"]:
            item = DictParser.parse(store)
            item["name"] = store["nom"]
            item["city"] = store["ville"]
            item["postcode"] = store["cp"]
            item["street_address"] = store["adresse"]
            oh = OpeningHours()
            tt = re.findall(r"(\w\w\.: \d\d:\d\d\-\d\d:\d\d|\w\w\.:\s\w+)", store["text1"])
            for i in tt:
                day, time = i.split(".:")
                if time in ["Gesloten", "GESLOTEN", "Closed", "CLOSED", "", " Closed"]:
                    continue

                open_time, close_time = time.split("-")
                day = sanitise_day(day)
                oh.add_range(day, open_time.strip(), close_time.strip())
                item["opening_hours"] = oh
            apply_category(Categories.BANK, item)
            yield item
