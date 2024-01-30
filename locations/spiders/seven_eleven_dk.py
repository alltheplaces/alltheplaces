from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider


class SevenElevenDKSpider(Spider):
    name = "seven_eleven_dk"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://7eleven-prod.azurewebsites.net/api/stores/all"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            item["postcode"] = str(item.pop("postcode"))

            item["ref"] = location["storeNumber"]

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                if location["{}ClosedAllDay".format(day)]:
                    continue
                item["opening_hours"].add_range(
                    day,
                    location["{}OpeningTime".format(day)].replace(".", ":"),
                    location["{}ClosingTime".format(day)].replace(".", ":"),
                )

            if location["storeChainName"] == "Shell / 7-Eleven":
                fuel = item.deepcopy()
                fuel["ref"] = "{}-shell".format(fuel["ref"])
                fuel.update(ShellSpider.item_attributes)
                apply_category(Categories.FUEL_STATION, fuel)
                apply_yes_no(Extras.CAR_WASH, fuel, location["hasCarwash"])
                yield fuel

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
