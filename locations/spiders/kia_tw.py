import re
from html import unescape

from scrapy import Selector

from locations.hours import DAYS_CN, OpeningHours
from locations.spiders.kia_au import KiaAUSpider


class KiaTWSpider(KiaAUSpider):
    name = "kia_tw"
    start_urls = ["https://www.kia.com/api/kia_tw/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def post_process_feature(self, item, feature):
        if "0" not in item["phone"] or item["phone"].startswith("00"):
            item.pop("phone", None)
        if feature.get("openHours"):
            hours_text = unescape(
                re.sub(r"\s+", " ", " ".join(Selector(text=feature["openHours"]).xpath("//text()").getall()).strip())
            )
            hours_text = (
                re.sub(r"([^:~\d])\s*(\d)", r"\1: \2", hours_text)
                .replace("~", " - ")
                .replace("至", " - ")
                .replace("週六週日", "週六 - 週日")
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_CN)
        yield item
