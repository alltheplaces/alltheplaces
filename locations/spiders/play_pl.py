from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PlayPLSpider(Spider):
    name = "play_pl"
    start_urls = ["https://www.play.pl/binaries/content/assets/play-common/data.json"]
    item_attributes = {"brand": "Play", "brand_wikidata": "Q7202998"}

    def parse(self, response, **kwargs):
        for index, feature in enumerate(response.json()):
            item = DictParser.parse(feature)
            item["ref"] = str(index)  # Might not be stable
            monFriRange = feature["mon-fri"].split("-")
            satRange = feature["sat"].split("-")
            sunRange = feature["sun"].split("-")
            item["opening_hours"] = OpeningHours()
            if len(monFriRange) == 2:
                item["opening_hours"].add_days_range(
                    days=DAYS[:5], open_time=monFriRange[0].strip(), close_time=monFriRange[1].strip()
                )
            else:
                continue
            if len(satRange) == 2:
                item["opening_hours"].add_range(day="Sa", open_time=satRange[0].strip(), close_time=satRange[1].strip())
            if len(sunRange) == 2:
                item["opening_hours"].add_range(day="Su", open_time=sunRange[0].strip(), close_time=sunRange[1].strip())
            yield item
