import scrapy
from scrapy.http import HtmlResponse

from locations.categories import Categories, apply_category, apply_yes_no, Extras
from locations.hours import DAYS_BG, OpeningHours
from locations.user_agents import BROWSER_DEFAULT
from locations.items import Feature

class FibankBGSpider(scrapy.Spider):
    name = "fibank_bg"
    item_attributes = {"brand": "Fibank", "brand_wikidata": "Q3367065"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.fibank.bg/bg/branch_network_xhr?method=get_locations"
        headers = {
            "x-requested-with": "XMLHttpRequest",
            "User-Agent": BROWSER_DEFAULT
        }
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

                    textResponse = HtmlResponse(url="my HTML string", body=location["text"], encoding='utf-8')
                    item["phone"] = textResponse.xpath('//div.phones/text()').get("").replace("/", "").replace(" ", "")
                    worktime = textResponse.xpath('//div.worktime/text()').get()
                    if worktime is not None:
                        days, times = worktime.replace("ч.", "").replace(" ", "").split(":", 1)
                        days = days.split("-")
                        days = [sanitise_day(days[0], DAYS_BG), sanitise_day(days[1], DAYS_BG)]
                        hours = hours.split("-");
                        item["opening_hours"] = OpeningHours()
                        item["opening_hours"].add_days_range(day_range(days[0], days[1]), hours[0], hours[1])
                else:
                    apply_category(Categories.ATM, item)
                    apply_yes_no("authentication:contactless", item, "atm_filter_contactless" in location["features"])
                    apply_yes_no(Extras.CASH_IN, item, "atm_filter_deposit" in location["features"])
                    # apply_yes_no("???", item, "atm_filter_blind" in location["features"])
                yield item
