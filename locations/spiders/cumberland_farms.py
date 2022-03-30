# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class CumberlandFarmsSpider(scrapy.Spider):
    name = "cumberland_farms"
    item_attributes = {"brand": "Cumberland Farms", "brand_wikidata": "Q1143685"}
    allowed_domains = ["cumberlandfarms.com"]

    start_urls = ["https://www.cumberlandfarms.com/storedata/getstoredatabylocation"]

    def parse(self, response):
        for store in response.json():
            if "StoreId" not in store:
                continue

            yield GeojsonPointItem(
                ref=store["StoreId"],
                lon=store["Longitude"],
                lat=store["Latitude"],
                name=f"Cumberland Farms #{store['StoreId']}",
                addr_full=store["Address"],
                city=store["City"],
                state=store["State"],
                postcode=store["Zip"],
                country="US",
                phone=store["Phone"],
                opening_hours="24/7" if store["Hours24"] else None,
                website=f"https://www.cumberlandfarms.com{store['Url']}",
                extras={
                    "amenity:fuel": store["Gas"] == "Y",
                    "amenity:chargingstation": store["EvChargingStations"] == "Y",
                    "fuel:diesel": store["Diesel"] == "Y",
                    "fuel:propane": store["Propane"] == "Y",
                    "atm": store["Atm"] == "Y",
                },
            )
