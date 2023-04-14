from scrapy import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class PearleStudioNLSpider(Spider):
    name = "pearle_studio_nl"
    item_attributes = {"brand": "Pearle Studio", "brand_wikidata": "Q117462110"}
    start_urls = ["https://grandvision.s3.amazonaws.com/ps/stores/json/ps_stores.json?storeList=PS"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location["u_smd_storenumber"]
            item["lat"] = location["u_smd_lat"]
            item["lon"] = location["u_smd_lon"]
            item["name"] = location["u_smd_storename"]
            item["housenumber"] = location["u_smd_addressnumber"]
            item["street"] = location["u_smd_address"]
            item["city"] = location["u_smd_city"]
            item["state"] = location["u_smd_province"]
            item["postcode"] = location["u_smd_postalcode"]
            item["website"] = location["u_smd_urlstore"]
            item["email"] = location["u_smd_emailstore"]
            item["phone"] = location["u_smd_phone"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if times := location.get(f"u_smd_sal_{day.lower()}"):
                    if times == "Gesloten":
                        continue
                    start_time, end_time = times.split(" - ")
                    item["opening_hours"].add_range(day, start_time, end_time)

            yield item
