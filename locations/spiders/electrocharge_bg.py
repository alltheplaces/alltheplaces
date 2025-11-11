import scrapy

from locations.items import Feature


class ElectrochargeBGSpider(scrapy.Spider):
    name = "electrocharge_bg"
    item_attributes = {"brand": "Electrocharge", "brand_wikidata": "Q133307258", "country": "BG"}
    allowed_domains = ["electrocharge.bg"]
    start_urls = ["https://electrocharge.bg/bg/electrocharge/fetch_charging_stations/"]
    no_refs = True

    def parse(self, response):
        data = response.json()
        for station in data["stations"]:
            item = Feature()
            item["addr_full"] = station["location"]
            item["lat"] = station["coordinates"]["lat"]
            item["lon"] = station["coordinates"]["lng"]
            yield item
