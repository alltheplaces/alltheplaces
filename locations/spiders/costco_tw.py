from locations.hours import DAYS_CN, OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoTWSpider(CostcoAUSpider):
    name = "costco_tw"
    allowed_domains = ["www.costco.com.tw"]
    stores_url = (
        "https://www.costco.com.tw/rest/v2/taiwan/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
    days = DAYS_CN

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            day_name = self.days[rule["weekDay"].removesuffix(".").title()]
            if rule.get("closed"):
                oh.set_closed(day_name)
            else:
                # Note: raw data contains errors where, for example, opening
                # times have the "PM" prefix ("下午"). It's necessary to
                # ignore all "AM" and "PM" prefixes from the raw data.
                oh.add_range(
                    day_name,
                    rule["openingTime"]["formattedHour"].removeprefix("上午 ").removeprefix("下午 ") + " AM",
                    rule["closingTime"]["formattedHour"].removeprefix("下午 ").removeprefix("上午 ") + " PM",
                    self.time_format,
                )
        return oh
