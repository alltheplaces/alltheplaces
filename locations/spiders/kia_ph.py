import re
from html import unescape

from scrapy import Selector

from locations.hours import OpeningHours
from locations.spiders.kia_au import KiaAUSpider


class KiaPHSpider(KiaAUSpider):
    name = "kia_ph"
    start_urls = ["https://www.kia.com/api/kia_philippines/base/fd01/findDealer.selectFindDealerAllList?isAll=true"]

    def post_process_feature(self, item, feature):
        item["phone"] = item["phone"].split("/", 1)[0].strip()
        if feature.get("openHours"):
            hours_text = unescape(
                re.sub(r"\s+", " ", " ".join(Selector(text=feature["openHours"]).xpath("//text()").getall()).strip())
            )
            if re.match(r"^\d", hours_text):
                hours_text = f"Monday - Friday: {hours_text}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)
        yield item
