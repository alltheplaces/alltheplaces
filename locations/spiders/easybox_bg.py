import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class easyboxBGSpider(scrapy.Spider):
    name = "easybox_bg"
    item_attributes = {"brand": "easybox", "brand_wikidata": "Q114496224"}
    allowed_domains = ["sameday.bg"]
    start_urls = ["https://sameday.bg/wp/wp-admin/admin-ajax.php?action=get_ooh_lockers_request&country=Bulgaria"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "BG"

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["image"] = "https://sameday.bg" + location["photo"]
            item["opening_hours"] = OpeningHours()
            for day in location["schedule"]:
                item["opening_hours"].add_range(DAYS[day["day"] - 1], day["openingHour"], day["closingHour"])
            yield item
