import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VodafoneItSpider(scrapy.Spider):
    name = "vodafone_it"
    item_attributes = {
        "brand": "Vodafone",
        "brand_wikidata": "Q122141",
    }
    allowed_domains = ["vodafone.it"]
    start_urls = ["https://negozi.vodafone.it/d/index"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data.get("profile"))
            item["ref"] = data.get("url")
            if data.get("profile", {}).get("mainPhone", {}):
                item["phone"] = data.get("profile", {}).get("mainPhone", {}).get("number")
            item["website"] = f'https://negozi.vodafone.it/{data.get("url")}'
            item["lat"] = data.get("profile", {}).get("yextDisplayCoordinate", {}).get("lat")
            item["lon"] = data.get("profile", {}).get("yextDisplayCoordinate", {}).get("long")
            oh = OpeningHours()
            if data.get("profile", {}).get("hours", {}):
                for open_hour in data.get("profile", {}).get("hours", {}).get("normalHours"):
                    for i in range(len(open_hour.get("intervals"))):
                        start = str(open_hour.get("intervals", {})[i].get("start")).zfill(4)
                        end = str(open_hour.get("intervals", {})[i].get("end")).zfill(4)
                        oh.add_range(
                            day=open_hour.get("day"),
                            open_time=f"{start[:2]}:{start[2:]}",
                            close_time=f"{end[:2]}:{end[2:]}",
                        )

            yield item
