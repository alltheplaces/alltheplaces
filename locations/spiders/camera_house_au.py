from scrapy import Spider

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CameraHouseAUSpider(Spider):
    name = "camera_house_au"
    item_attributes = {
        "brand": "Camera House",
        "brand_wikidata": "Q124062505",
        "extras": {
            "shop": "camera",
        },
    }
    allowed_domains = ["www.camerahouse.com.au"]
    start_urls = ["https://www.camerahouse.com.au/stores/index/dataAjax"]

    def parse(self, response):
        for location in response.json():
            properties = {
                "ref": location["i"],
                "name": location["n"],
                "lat": location["l"],
                "lon": location["g"],
                "addr_full": location["a"],
                "street_address": clean_address([location["fa"].get("st"), location["fa"].get("st2")]),
                "city": location["fa"]["su"],
                "state": location["fa"]["rc"],
                "postcode": location["fa"]["po"],
                "phone": location["p"],
                "email": location["e"],
                "website": "https://www.camerahouse.com.au" + location["u"],
            }
            properties["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_hours in list(filter(None, map(str.strip, location["oh"].split(",")))):
                if "CLOSED" in day_hours.upper():
                    continue
                day_name = DAYS_3_LETTERS_FROM_SUNDAY[int(day_hours.split("|", 1)[0])]
                start_time, end_time = day_hours.split("|", 1)[1].split("-", 1)
                hours_string = f"{hours_string} {day_name}: {start_time} - {end_time}"
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
