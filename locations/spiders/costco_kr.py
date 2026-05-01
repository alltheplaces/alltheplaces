from locations.hours import DAYS_KR, OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoKRSpider(CostcoAUSpider):
    name = "costco_kr"
    allowed_domains = ["www.costco.co.kr"]
    stores_url = (
        "https://www.costco.co.kr/rest/v2/korea/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
    days = DAYS_KR

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            day_name = self.days[rule["weekDay"].removesuffix(".").title()]
            if rule.get("closed"):
                oh.set_closed(day_name)
            else:
                # Note: raw data contains errors where, for example, opening
                # times have the "PM" prefix ("오후"). It's necessary to
                # ignore all "AM" and "PM" prefixes from the raw data.
                oh.add_range(
                    day_name,
                    rule["openingTime"]["formattedHour"].removeprefix("오전 ").removeprefix("오후 ") + " AM",
                    rule["closingTime"]["formattedHour"].removeprefix("오후 ").removeprefix("오전 ") + " PM",
                    self.time_format,
                )
        return oh
