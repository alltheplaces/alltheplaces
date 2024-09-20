import re
from typing import Iterable

from locations.items import Feature
from locations.spiders.five_guys_us import FIVE_GUYS_SHARED_ATTRIBUTES
from locations.storefinders.yext_answers import YextAnswersSpider

# Five Guys YextAnswers

FIVE_GUYS_INSTAGRAMS = [
    "fiveguysksa",
    "fiveguysuk",
    "fiveguysfrance",
    "fiveguys_es",
    "fiveguysbe",
    "fiveguysde",
    "fiveguysnl",
    "fiveguyslux",
    "fiveguysireland",
    "fiveguysca",
    "fiveguyshongkong",
    "fiveguysuae",
    "fiveguyssingapore",
    "fiveguysch",
    "fiveguysmy",
    "fiveguysqatar",
    "fiveguysaustralia",
    "fiveguysitaly",
    "fiveguysmacau",
    "fiveguys.korea",
    "fiveguys",
    "fiveguyskuwait",
]

FIVE_GUYS_TWITTERS = [
    "FiveGuys",
    "FiveGuysUK",
    "FiveGuysDe ",
    "FiveGuysNl ",
    "fiveguyslux ",
    "FiveGuysCanada ",
    "FiveGuysIre ",
    "FiveGuysUAE ",
    "FiveGuysMY ",
    "FiveGuysQatar ",
    "FiveGuysKSA ",
    "FiveGuysItaly ",
    "FiveGuysKuwait ",
]


class FiveGuysAUSpider(YextAnswersSpider):
    name = "five_guys_au"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    api_key = "e9a586fc4400f344829f350f07a7e367"
    experience_key = "search-backend-au"
    locale = "en"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("name")
        if location.get("c_pagesURL") is not None:
            item["website"] = location["c_pagesURL"]
        elif re.match(r"^https:\/\/(www.)?fiveguys\.[\w\.]+\/?", item["website"]):
            if item["website"].endswith("/"):
                item["website"] = item["website"] + location["slug"]
            else:
                item["website"] = item["website"] + "/" + location["slug"]
        self.process_websites(item)
        if item.get("twitter") in FIVE_GUYS_TWITTERS:
            item.pop("twitter")
        if item["extras"].get("contact:instagram") in FIVE_GUYS_INSTAGRAMS:
            item["extras"].pop("contact:instagram")
        yield item

    def process_websites(self, item: Feature) -> None:
        """Override with any changes for websites, e.g. multiple languages"""
        return
