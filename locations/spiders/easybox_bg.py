import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class EasyboxBGSpider(scrapy.Spider):
    name = "easybox_bg"
    item_attributes = {"brand": "easybox", "brand_wikidata": "Q114496224"}
    allowed_domains = ["sameday.bg"]
    start_urls = ["https://sameday.bg/wp/wp-admin/admin-ajax.php?action=get_ooh_lockers_request&country=Bulgaria"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "BG"
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            apply_category(Categories.PARCEL_LOCKER, item)
            item["image"] = "https://sameday.bg" + location["photo"]
            item["opening_hours"] = OpeningHours()
            for day_schedule in location["schedule"]:
                day = DAYS[day_schedule["day"] - 1]
                opening_hour = day_schedule["openingHour"].rsplit(":", 1)[0]
                closing_hour = day_schedule["closingHour"].rsplit(":", 1)[0]
                item["opening_hours"].add_range(day, opening_hour, closing_hour)
            yield item
