import json
import re
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST


class LaHalleFRSpider(Spider):
    name = "la_halle_fr"
    item_attributes = {"brand": "La Halle", "brand_wikidata": "Q100728296"}
    start_urls = [
        "https://www.lahalle.com/on/demandware.store/Sites-LHA_FR_SFRA-Site/fr_FR/Stores-FindStores?showMap=true&lat=48.85349504454055&long=2.3483914659676657&radius=10000"
    ]
    allowed_domains = ["www.lahalle.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": FIREFOX_LATEST}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            store["street-address"] = merge_address_lines([store.pop("address1", ""), store.pop("address2", "")])
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["state"] = store["custom"]["BMNR_StateName"]
            state_code = store["custom"]["BMNR_StateCode"]
            item[
                "website"
            ] = f'https://www.lahalle.com/magasins-{item["state"]}-{state_code}-{item["branch"]}-{item["ref"]}.html'.lower().replace(
                " ", "-"
            )
            item["opening_hours"] = OpeningHours()
            opening_hours = json.loads(store["custom"]["BMNR_horaires"])
            for day, hours in opening_hours.items():
                if day := sanitise_day(day, DAYS_FR):
                    shift_1_open_time, shift_1_close_time = hours.get("ouverture_matin"), hours.get(
                        "fermeture_matin"
                    ) or hours.get("fermeture_apresmidi")
                    shift_2_open_time, shift_2_close_time = hours.get("ouverture_apresmidi"), hours.get(
                        "fermeture_apresmidi"
                    )
                    for shift_timing in [
                        (shift_1_open_time, shift_1_close_time),
                        (shift_2_open_time, shift_2_close_time),
                    ]:
                        if shift_timing[0] and shift_timing[1]:
                            item["opening_hours"].add_range(
                                day, self.clean_hours(shift_timing[0]), self.clean_hours(shift_timing[1])
                            )
            yield item

    def clean_hours(self, hours: str) -> str:
        if not hours:
            return ""
        hours = re.sub(r"(\d{2})(\d{2})", r"\1:\2", hours)
        return hours
