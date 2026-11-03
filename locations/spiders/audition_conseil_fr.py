import json
import re
from typing import Any, Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class AuditionConseilFRSpider(Spider):
    name = "audition_conseil_fr"
    item_attributes = {"brand": "Audition Conseil", "brand_wikidata": "Q104904635"}
    allowed_domains = ["www.auditionconseil.fr"]
    start_urls = ["https://www.auditionconseil.fr/les-centres/"]
    # Matches "9h à 12h30", "14h - 18h", "9h-12h", "14à 18h" and "9h à 12"
    TIME_RANGE = re.compile(r"(\d{1,2})\s*(?:h\s*(\d{2})?)?\s*(?:à|-|–)\s*(\d{1,2})\s*(?:h\s*(\d{2})?)?", re.I)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        markers = json.loads(re.search(r"window\.initialMarkers = (\[.*?\]);\s*$", response.text, re.M).group(1))
        for marker in markers:
            popup = Selector(text=marker["popup"])
            item = Feature()
            item["ref"] = popup.xpath('//div[starts-with(@id, "carousel-")]/@id').get().removeprefix("carousel-")
            item["website"] = popup.xpath("//strong/a/@href").get()
            item["branch"] = re.sub(
                r"^Audition Conseil\s+", "", popup.xpath("//strong/a/text()").get().strip(), flags=re.I
            )
            item["lat"] = marker["lat"]
            item["lon"] = marker["lng"]

            address = " ".join(popup.xpath('//span[@class="pop-adr"]/text()').get("").split())
            item["addr_full"] = address
            if m := re.search(r"(\d{5}),?\s*([^,\d][^,]*)$", address):
                item["postcode"], item["city"] = m.group(1), m.group(2).strip()
                item["country"] = OVERSEAS_COUNTRIES.get(item["postcode"][:3], "FR")

            item["phone"] = popup.xpath('//a[starts-with(@href, "tel:")]/@href').get("")
            item["email"] = popup.xpath('//a[starts-with(@href, "mailto:")]/@href').get("")

            yield response.follow(item["website"], self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        oh = OpeningHours()
        for row in response.xpath('//div[@class="liste-horraires"]//div[@class="time-item"]'):
            day = sanitise_day(row.xpath("./strong/text()").get(""), DAYS_FR)
            times = row.xpath("./small/text()").get("")
            if not day:
                continue
            # Appointment only slots and alternate week openings are not regular opening hours
            if re.search(r"rendez-vous|rdv|semaines", times, re.I):
                continue
            if "fermé" in times.lower():
                oh.set_closed(day)
                continue
            for open_h, open_m, close_h, close_m in self.TIME_RANGE.findall(times):
                oh.add_range(day, f"{open_h}:{open_m or '00'}", f"{close_h}:{close_m or '00'}")
        item["opening_hours"] = oh
        yield item
