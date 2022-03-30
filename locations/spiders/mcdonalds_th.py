import re
import scrapy
from locations.items import GeojsonPointItem


class McDonaldsTHSpider(scrapy.Spider):
    name = "mcdonalds_th"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["api.buzzebees.com"]

    start_urls = (
        "https://api.buzzebees.com/api/place/?device_app_id=682039088498074&agencyId=8510&require_campaign=false&top=300&bzbTime=1513692783949",
    )

    def normalize_time(self, time_str, flag):
        match = re.search(r"([0-9]{1,2}).([0-9]{1,2})", time_str)
        h, m = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if flag and int(h) < 13 else int(h),
            int(m),
        )

    def store_hours(self, data):
        if "24" in data:
            return "24/7"

        data = data.split("-")
        start = data[0].strip()
        end = data[1].strip()
        start = self.normalize_time(start, False)
        end = self.normalize_time(end, True)

        return "Mo-Su:" + "{}-{}".format(start, end)

    def parse(self, response):
        stores = response.json()
        for data in stores:
            properties = {
                "ref": data["id"],
                "addr_full": data["description_en"],
                "name": data["name_en"],
                "lat": data["location"]["latitude"],
                "lon": data["location"]["longitude"],
                "phone": data["contact_number"],
            }

            opening_hours = self.store_hours(data["working_day_en"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
