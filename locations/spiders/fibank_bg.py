import scrapy
from scrapy import Selector

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_BG, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class FibankBGSpider(scrapy.Spider):
    name = "fibank_bg"
    item_attributes = {"brand": "Fibank", "brand_wikidata": "Q3367065"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.fibank.bg/bg/branch_network_xhr?method=get_locations"
        headers = {"x-requested-with": "XMLHttpRequest", "User-Agent": BROWSER_DEFAULT}
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        cities = response.json()
        for city in cities:
            for location in city["city_locations"]:
                item = Feature()
                item["ref"] = location["id"]
                item["lat"], item["lon"] = location["coords"].split(",")
                item["name"] = location["name"]
                item["addr_full"] = location["address"]

                if location["type"] == 1:
                    apply_category(Categories.BANK, item)

                    textResponse = Selector(text=location["text"])
                    item["phone"] = (
                        textResponse.xpath("//div[contains(@class, 'phones')]/text()").get().replace("/", "")
                    )
                    worktime = textResponse.xpath("//div[contains(@class, 'worktime')]/text()").get()
                    isUnparsable = "зимен" in worktime or "и " in worktime or "събота" in worktime or ", " in worktime
                    if worktime is not None and not isUnparsable:
                        days, hours = worktime.replace("ч", "").replace(" ", "").replace(".", "").split(":", 1)
                        days = days.split("-")
                        days = [sanitise_day(days[0], DAYS_BG), sanitise_day(days[1], DAYS_BG)]
                        hours = hours.split("-")
                        item["opening_hours"] = OpeningHours()
                        item["opening_hours"].add_days_range(day_range(days[0], days[1]), hours[0], hours[1])
                else:
                    apply_category(Categories.ATM, item)
                    apply_yes_no("authentication:contactless", item, "atm_filter_contactless" in location["features"])
                    apply_yes_no(Extras.CASH_IN, item, "atm_filter_deposit" in location["features"])
                    # apply_yes_no("???", item, "atm_filter_blind" in location["features"])
                yield item
