import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OzkBankUSSpider(CrawlSpider, StructuredDataSpider):
    name = "ozk_bank_us"
    item_attributes = {"brand": "Bank OZK", "brand_wikidata": "Q20708654"}
    start_urls = ["https://www.ozk.com/locations/locations-list/"]
    rules = [
        Rule(LinkExtractor(r"/locations-list/\w\w$")),
        Rule(LinkExtractor(r"/locations-list/\w\w/[^/]+$")),
        Rule(LinkExtractor(r"/locations/\w\w/[^/]+/[^/]+/?$"), "parse"),
    ]
    wanted_types = ["BankOrCreditUnion"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["phone"] == "+17702928000":
            return  # Duplicate ld json on every page

        if data := response.xpath('//div[@class="store-hours drive hours-box"]//astro-island/@props').get():
            atm = Feature()
            atm["opening_hours"] = self.parse_opening_hours(json.loads(data))
            atm["ref"] = "{}-ATM".format(item["ref"])
            atm["lat"] = item["lat"]
            atm["lon"] = item["lon"]

            apply_category(Categories.ATM, atm)
            apply_yes_no(Extras.DRIVE_THROUGH, atm, True)

            yield atm

        apply_category(Categories.BANK, item)
        yield item

    def parse_opening_hours(self, data: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rules in data["hours"][1].items():
            if rules[1]["status"][1] == "Closed":
                oh.set_closed(day)
            else:
                for times in rules[1]["blocks"][1]:
                    end_time = times[1]["to"][1]
                    if end_time == "2400":
                        end_time = "2359"
                    oh.add_range(day, times[1]["from"][1], end_time, "%H%M")
        return oh
