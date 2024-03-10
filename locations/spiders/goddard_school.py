import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class GoddardSchoolSpider(scrapy.Spider):
    name = "goddard_school"
    item_attributes = {"brand": "Goddard School", "brand_wikidata": "Q5576260"}
    allowed_domains = ["goddardschool.com"]
    start_urls = ["https://www.goddardschool.com/apps/gsi/api/v1/schools"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        for data in response.json().get("items"):
            item = DictParser.parse(data.get("address1"))
            item["ref"] = data.get("fmsId")
            item["email"] = data.get("emailAddress")
            item["phone"] = data.get("telephone")
            item["website"] = response.urljoin(data.get("url"))
            oh = OpeningHours()
            if data.get("hours"):
                for day in DAYS:
                    oh.add_range(
                        day=day,
                        open_time=data.get("hours").split(" - ")[0],
                        close_time=data.get("hours").split(" - ")[1],
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
