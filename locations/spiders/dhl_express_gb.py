import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DhlExpressGbSpider(scrapy.Spider):
    name = "dhl_express_gb"
    item_attributes = {"brand": "DHL", "brand_wikidata": "Q489815"}
    allowed_domains = ["dhlparcel.co.uk"]

    def start_requests(self):
        url = "https://track.dhlparcel.co.uk/UKMail/Handlers/DepotData"
        yield scrapy.Request(url=url, method="POST")

    def parse(self, response):
        for data in response.json():
            item = Feature()
            item["ref"] = data.get("DepotNumber")
            item["name"] = data.get("DepotName")
            item["postcode"] = data.get("DepotAddress", {}).get("Postcode")
            item["country"] = data.get("DepotAddress", {}).get("Country")
            item["city"] = data.get("DepotAddress", {}).get("PostalTown")
            item["street_address"] = data.get("DepotAddress", {}).get("Address1")
            item["lat"] = data.get("Latitude")
            item["lon"] = data.get("Longitude")
            item["phone"] = data.get("Telephone")
            oh = OpeningHours()
            for day in data.get("OpeningTimes"):
                oh.add_range(
                    day=DAYS[day.get("Day") - 1], open_time=day.get("OpenTime"), close_time=day.get("CloseTime")
                )
            item["opening_hours"] = oh.as_opening_hours()
            apply_category(Categories.POST_OFFICE, item)

            yield item
