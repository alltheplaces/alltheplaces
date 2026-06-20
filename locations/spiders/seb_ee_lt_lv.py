from typing import Any, AsyncIterator
from urllib.parse import parse_qs, urlparse

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EE, DAYS_LT, OpeningHours, day_range
from locations.items import Feature


class SebEELTLVSpider(Spider):
    name = "seb_ee_lt_lv"
    item_attributes = {"brand": "SEB", "brand_wikidata": "Q975655"}
    day_labels = {
        "EE": DAYS_EE | {"E": "Mo", "T": "Tu", "K": "We", "N": "Th", "R": "Fr", "L": "Sa", "P": "Su"},
        "LT": DAYS_LT | {"P": "Mo", "A": "Tu", "T": "We", "Pn": "Fr", "\u0160": "Sa", "S": "Su"},
        "LV": {"P": "Mo", "O": "Tu", "T": "We", "C": "Th", "Pk": "Fr", "S": "Sa", "Sv": "Su"},
    }

    async def start(self) -> AsyncIterator[Any]:
        for cc in ("ee", "lt", "lv"):
            for type_id in (1, 2):
                yield Request(url=f"https://www.seb.{cc}/atm-find?type_id={type_id}&page=0")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        parsed = urlparse(response.url)
        country = (parsed.hostname or "").rsplit(".", 1)[-1].upper()
        type_id = parse_qs(parsed.query).get("type_id", [None])[0]

        for card in response.xpath('//*[contains(@class, "c-atm-search__item")]'):
            map_href = card.xpath('.//a[contains(@href, "google.com/maps")]/@href').get()
            map_query = parse_qs(urlparse(map_href or "").query)
            lat, _, lon = (map_query.get("query") or map_query.get("destination") or [""])[0].partition(",")
            if not (lat and lon):
                self.logger.error("Missing coordinates on {}".format(response.url))
                continue

            # Source is HTML, not JSON, and the markup has no stable node ID.
            item = Feature(
                ref=f"{country}-{type_id}-{lat},{lon}",
                branch=card.xpath("normalize-space(.//h5)").get(),
                lat=lat,
                lon=lon,
                country=country,
            )

            # Address text is freeform; do not split on commas into structured fields.
            item["addr_full"] = card.xpath(
                'normalize-space((.//*[contains(@class, "col-md-6")])[2]//*[contains(@class, "mb-2")][1])'
            ).get()
            if opening_hours := self.parse_hours(card, country):
                item["opening_hours"] = opening_hours

            if type_id == "1":
                apply_category(Categories.ATM, item)
            elif type_id == "2":
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected type_id: {}".format(type_id))
                continue

            yield item

        if next_href := response.xpath('//*[contains(@class, "pager__item--next")]//@href').get():
            yield response.follow(next_href)

    def parse_hours(self, card: Any, country: str) -> OpeningHours | None:
        opening_hours = OpeningHours()
        for row in card.xpath('.//*[contains(@class, "office-hours__item")]'):
            day_label = row.xpath('normalize-space(.//*[contains(@class, "office-hours__item-label")])').get()
            time_slot = row.xpath('normalize-space(.//*[contains(@class, "office-hours__item-slots")])').get()
            if not (day_label and time_slot):
                continue
            try:
                days = self.parse_days(country, day_label)
                if time_slot == "24H":
                    opening_hours.add_days_range(days, "00:00", "24:00")
                else:
                    opening_hours.add_days_range(days, *time_slot.split("-", 1))
            except Exception:
                self.logger.error("Unable to parse opening hours: {} {} {}".format(country, day_label, time_slot))
                return None

        return opening_hours or None

    def parse_days(self, country: str, day_label: str) -> list[str]:
        day_labels = self.day_labels[country]
        if "-" in day_label:
            start_day, end_day = day_label.split("-", 1)
            return day_range(day_labels[start_day], day_labels[end_day])
        return [day_labels[day_label]]
