from scrapy import Request
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class SuitsupplySpider(Spider):
    name = "suitsupply"
    item_attributes = {"brand": "Suitsupply", "brand_wikidata": "Q17149142"}
    # Get a list of countries
    start_urls = ["https://suitsupply.com/en-nl/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for button in response.css("button.js-country-locator-link"):
            yield Request(
                f"https://suitsupply.com/on/demandware.store/Sites-INT-Site/en_NL/Stores-FindStores?showMap=false&country={button.xpath('@data-option').get()}",
                callback=self.parse_locations,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

    def parse_locations(self, response):
        # This part doesn't have all the stores shown on the website, but it does have a lot more useful information.
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["website"] = f"https://suitsupply.com/en-nl/stores/{item['ref'].removeprefix('stores-')}"

            oh = OpeningHours()
            for data in location["storeHoursData"]:
                if data["open"] != "--:--":
                    oh.add_range(DAYS_3_LETTERS_FROM_SUNDAY[int(data["day"])], data["open"], data["close"])
            item["opening_hours"] = oh

            yield item
