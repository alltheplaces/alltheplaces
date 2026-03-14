import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature


class AlstomSpider(scrapy.Spider):
    name = "alstom"
    item_attributes = {"brand": "Alstom", "brand_wikidata": "Q309084"}
    allowed_domains = ["alstom.com"]
    start_urls = ("https://www.alstom.com/alstom-page/maps/json/1826",)

    def parse(self, response):
        for i in response.json():
            for j in i["locations"]:
                try:
                    lng = float(j["long"])
                except:
                    lng = j["long"].replace(",", "").replace(".", "")
                    lng = lng[:3] + "." + lng[3:]
                try:
                    lat = float(j["lat"].strip("\u200b"))
                except:
                    lat = j["lat"].replace(",", "").replace(".", "")
                    lat = lat[:3] + "." + lat[3:]
                if not j["address"]:
                    j["address"] = ""
                addr = Selector(text=j["address"]).xpath("//p/text()").get()

                properties = {
                    "ref": j["id"],
                    "name": j["title"],
                    "addr_full": addr,
                    "country": i["name"],
                    "phone": j["phone"] or None,
                    "lat": float(lat),
                    "lon": float(lng),
                }

                apply_category(Categories.OFFICE_COMPANY, properties)

                yield Feature(**properties)
