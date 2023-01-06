import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROSWER_DEFAULT


class PullAndBearSpiderFR(scrapy.Spider):
    name = "pull_and_bear_fr"
    item_attributes = {
        "brand": "Pull&Bear",
        "brand_wikidata": "Q691029",
    }
    allowed_domains = ["pullandbear.com"]
    start_urls = [
        "https://www.pullandbear.com/itxrest/2/bam/store/24009404/physical-stores-by-country?countryCode=FR&appId=1"
    ]
    user_agent = BROSWER_DEFAULT

    def parse(self, response):
        for data in response.json().get("stores"):
            item = DictParser.parse(data)

            item["phone"] = data.get("phones")[0]
            item["street_address"] = data.get("addressLines")[0]

            oh = OpeningHours()
            for openHour in data.get("openingHours", {}).get("schedule"):
                for day in openHour.get("weekdays"):
                    oh.add_range(
                        day=DAYS[day - 1],
                        open_time=openHour.get("timeStripList")[0].get("initHour"),
                        close_time=openHour.get("timeStripList")[0].get("endHour"),
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
