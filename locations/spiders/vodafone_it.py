from typing import Iterable

from locations.items import Feature
from locations.spiders.vodafone_de import VODAFONE_SHARED_ATTRIBUTES
from locations.storefinders.yext_answers import YextAnswersSpider


class VodafoneITSpider(YextAnswersSpider):
    name = "vodafone_it"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    api_key = "07377ddb3ff87208d4fb4d14fed7c6ff"
    experience_key = "store-locator-basic-search"
    locale = "it"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        self.crawler.stats.inc_value("x/c_storeType/{}".format(location["data"].get("c_storeType")))
        if location["data"].get("c_storeType") != "Vodafone Store":
            return None

        item["branch"] = item.pop("name").removeprefix("Vodafone Store").strip(" |")
        yield item
