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
            mon_fri_range = feature["mon-fri"].split("-")
            sat_range = feature["sat"].split("-")
            sun_range = feature["sun"].split("-")
            item["opening_hours"] = OpeningHours()
            if len(mon_fri_range) == 2:
                item["opening_hours"].add_days_range(
                    days=DAYS[:5], open_time=mon_fri_range[0].strip(), close_time=mon_fri_range[1].strip()
                )
            else:
                continue
            if len(sat_range) == 2:
                item["opening_hours"].add_range(
                    day="Sa", open_time=sat_range[0].strip(), close_time=sat_range[1].strip()
                )
            if len(sun_range) == 2:
                item["opening_hours"].add_range(
                    day="Su", open_time=sun_range[0].strip(), close_time=sun_range[1].strip()
                )
            yield item
