import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class ChangeGroupGBSpider(Spider):
    name = "change_group"
    item_attributes = {"brand": "Change Group", "brand_wikidata": "Q5071758"}
    start_urls = ["https://uk.changegroup.com/slatwall/?slatAction=changeGroup:main.globalBranchData"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data=response.text.encode("utf-8")
        for country in json.loads(data)["countries"]:
            for region in country["regions"]:
                for location in region["branches"]:
                    item = DictParser.parse(location)
                    item["street_address"] = merge_address_lines([location.pop("streetAddress"), location.pop("streetAddress2")]
                    apply_category(Categories.BUREAU_DE_CHANGE, item)
                    oh = OpeningHours()
                    for day in DAYS_FULL:
                        open = location["openingHours"][day.lower()]["open"].replace(" am","").strip()
                        close = location["openingHours"][day.lower()]["close"].replace(" am","").strip()
                        if open == '24/7':
                            item["opening_hours"] = "24/7"
                        elif open == "24 Hours":
                            oh="24/7"
                        elif "to" in open:
                            open1,close1=open.split(" to ")
                            if not ("." or ":") in open1:
                                open1 = open1 + ":00"
                            if not ("." or ":") in close1:
                                close1 = close1 + ":00"
                            oh.add_range(day, open1.replace(".",":"), close1.replace(".",":"))
                            if "to" in close:
                                open2,close2=close.split(" to ")
                                if not ("." or ":") in open2:
                                    open2 = open2 + ":00"
                                    close2 = close2 + ":00"
                                oh.add_range(day, open2.replace(".",":"), close2.replace(".",":"))
                        elif close:
                            if "closed" in open.lower():
                                continue
                            openhour,openminutes=open.replace(".",":").replace(" pm","").split(":")
                            closehour,closeminutes=close.replace(".",":").replace(" pm","").split(":")
                            if "pm" in open:
                                openhour = int(openhour) + 12
                            if "pm" in close:
                                closehour = int(closehour) + 12
                            if ";" in open or ";" in close:
                                continue
                            if int(openhour) > 23 or int(closehour) > 23:
                                continue
                            oh.add_range(day, str(openhour) + ":" + str(openminutes), str(closehour) + ":" + str(closeminutes))
                        else:
                            continue
                    item["opening_hours"]=oh
                    yield item
