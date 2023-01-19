import json
import re

import scrapy

from locations.items import Feature


class ReebokSpider(scrapy.Spider):
    name = "reebok"
    item_attributes = {"brand": "Reebok", "brand_wikidata": "Q466183"}
    allowed_domains = ["reebok.com", "placesws.adidas-group.com"]
    start_urls = [
        "https://placesws.adidas-group.com/API/search?brand=reebok&geoengine=google&method=get&category=store&latlng=&page=1&pagesize=500&fields=name,street1,street2,addressline,buildingname,postal_code,city,state,store_o+wner,country,storetype,longitude_google,latitude_google,store_owner,state,performance,brand_store,factory_outlet,originals,neo_label,y3,slvr,children,woman,footwear,football,basketball,outdoor,porsche_design,miadidas,miteam,stella_mccartney,eyewear,micoach,opening_ceremony,operational_status,from_date,to_date,dont_show_country&format=json&storetype="
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        if not (data := json.loads(response.text.replace("\n", "")).get("wsResponse", {}).get("result")):
            return
        for row in data:
            if row.get("storetype") in ["franchise", "ownretail", "factoryoutlet", "Reebokretail", "Reebokoutlet"]:
                item = Feature()
                item["ref"] = row.get("id")
                item["name"] = row.get("name")
                item["city"] = row.get("city")
                item["country"] = row.get("country")
                item["postcode"] = row.get("postal_code")
                item["state"] = row.get("state")
                item["street_address"] = row.get("street1")
                item["lat"] = row.get("latitude_google")
                item["lon"] = row.get("longitude_google")

                yield item

        page = int(re.findall(r"page=[0-9]+", response.url)[-1][5:]) + 1
        url = f"https://placesws.adidas-group.com/API/search?brand=reebok&geoengine=google&method=get&category=store&latlng=&page={page}&pagesize=500&fields=name,street1,street2,addressline,buildingname,postal_code,city,state,store_o+wner,country,storetype,longitude_google,latitude_google,store_owner,state,performance,brand_store,factory_outlet,originals,neo_label,y3,slvr,children,woman,footwear,football,basketball,outdoor,porsche_design,miadidas,miteam,stella_mccartney,eyewear,micoach,opening_ceremony,operational_status,from_date,to_date,dont_show_country&format=json&storetype="
        yield scrapy.Request(url=url, callback=self.parse)
