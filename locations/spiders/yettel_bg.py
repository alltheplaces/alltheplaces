from scrapy import Spider

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class YettelBGSpider(Spider):
    name = "yettel_bg"
    item_attributes = {
        "brand": "Yettel",
        "brand_wikidata": "Q14915070",
        "country": "BG",
    }
    start_urls = ["https://www.yettel.bg/eshop/bff/v1/reactRequest/getStoresList"]
    no_refs = True
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        json_data = response.json()
        for store in json_data["stores"]:
            item = Feature()
            item["ref"] = store["id"]

            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            item["street_address"] = store["address"]["bg"]
            item["city"] = store["city"]["bg"]

            item["opening_hours"] = OpeningHours()
            mo_fr_hours = store["workingTimeMoFr"].replace(" ", "").replace("–", "-").lower()
            if "временнозатворен" in mo_fr_hours:
                # The store is temporarily closed, skip opening hours
                yield item
                continue
            if mo_fr_hours is not None and mo_fr_hours != "затворено":
                split = mo_fr_hours.split("-")
                opening_time = split[0]
                closing_time = split[1]
                item["opening_hours"].add_days_range(DAYS_WEEKDAY, opening_time, closing_time)
            elif mo_fr_hours == "затворено":
                item["opening_hours"].set_closed(DAYS_WEEKDAY)

            sat_hours = store["workingTimeSat"].replace(" ", "").lower()
            if sat_hours is not None and sat_hours != "затворено":
                split = sat_hours.split("-")
                opening_time = split[0]
                closing_time = split[1]
                item["opening_hours"].add_range('Sa', opening_time, closing_time)
            elif sat_hours == "затворено":
                item["opening_hours"].set_closed('Sa')

            sun_hours = store["workingTimeSun"].replace(" ", "").lower()
            if sun_hours is not None and sun_hours != "затворено":
                split = sun_hours.split("-")
                opening_time = split[0]
                closing_time = split[1]
                item["opening_hours"].add_range('Su', opening_time, closing_time)
            elif sun_hours == "затворено":
                item["opening_hours"].set_closed('Su')

            yield item
