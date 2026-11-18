import json
import re
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_FR, OpeningHours
from locations.items import Feature

DAY_NAMES = "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
DAY_SPEC = re.compile(rf"(?:\bdu\s+)?\b({DAY_NAMES})\b(?:\s*(?:au|à|-)\s*\b({DAY_NAMES})\b)?")
TIME = r"(\d{1,2})\s*(heures?|h|:)?\s*(\d{2})?"
TIME_RANGE = re.compile(rf"(?<!\d){TIME}\s*(?:-|–|à|a)\s*{TIME}(?!\d)")
APPOINTMENT = re.compile(r"\b(?:rdv|rv|rendez[\s-]vous)\b")
FILLER = re.compile(
    r"\b(?:en dehors de ces horaires|l'après[\s-]midi|après[\s-]midi|sur|et|de|du|le|les|la|l'|des)\b|[\s:/|,.;-]"
)


class NestennSpider(Spider):
    name = "nestenn"
    item_attributes = {"brand": "Nestenn", "brand_wikidata": "Q128788942", "name": "Nestenn"}
    start_urls = ["https://nestenn.com/liste-agences"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        emails = {}
        for card in response.xpath('//div[.//h3/a[contains(@href, "/liste-agences/")]]'):
            href = card.xpath(".//h3/a/@href").get()
            if mail_link := card.xpath('.//a[contains(@href, "contact-autre?mail=")]/@href').get():
                emails[href] = parse_qs(urlparse(mail_link).query).get("mail", [None])[0]

        for agency in json.loads(response.xpath("//@data-agences").get()):
            item = Feature()
            item["ref"] = agency["href"].rsplit("/", 1)[1]
            item["website"] = agency["href"]
            item["branch"] = agency["label"].strip()
            item["phone"] = agency["phone"]
            item["email"] = emails.get(agency["href"])
            if agency.get("photo") and not agency["photo"].endswith("defaut_logo_agence.jpg"):
                item["image"] = agency["photo"]

            address = re.sub(r"\s+", " ", agency["address"]).strip(" ,")
            street, _, locality = address.rpartition(",")
            item["street_address"] = street.strip(" ,") or None
            if m := re.fullmatch(r"(\d[\d-]*)\s+(.+)", locality.strip()):
                item["postcode"], item["city"] = m.groups()
            else:
                item["addr_full"] = address

            lat, lon = float(agency["lat"] or 0), float(agency["lng"] or 0)
            if lat and lon:
                item["lat"], item["lon"] = lat, lon

            apply_category(Categories.OFFICE_ESTATE_AGENT, item)
            yield Request(agency["href"], callback=self.parse_agency, cb_kwargs={"item": item})

    def parse_agency(self, response: Response, item: Feature) -> Iterable[Feature]:
        text = " ".join(
            response.xpath('//p[contains(., "Les horaires d\'ouverture")]/text()[preceding-sibling::br]').getall()
        )
        item["opening_hours"] = self.parse_hours(text)
        yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        """Parse the free text hours. Return None unless every part is understood.
        Days marked as appointment only are left out."""
        text = re.sub(r"\s+", " ", text.lower().replace("’", "'")).strip()
        days = list(DAY_SPEC.finditer(text))
        if not days or FILLER.sub("", text[: days[0].start()]):
            return None

        oh = OpeningHours()
        for i, day in enumerate(days):
            end = days[i + 1].start() if i + 1 < len(days) else len(text)
            segment = text[day.end() : end]
            first = DAYS_FR[day.group(1).title()]
            last = DAYS_FR[(day.group(2) or day.group(1)).title()]
            day_list = DAYS[DAYS.index(first) : DAYS.index(last) + 1]
            if not day_list:
                return None

            ranges = []
            for m in TIME_RANGE.finditer(segment):
                h1, u1, m1, h2, u2, m2 = m.groups()
                if not (u1 or u2) or int(h1) > 24 or int(h2) > 24:
                    return None
                ranges.append((f"{int(h1):02}:{m1 or '00'}", f"{int(h2):02}:{m2 or '00'}"))
            leftover = FILLER.sub("", APPOINTMENT.sub(" ", TIME_RANGE.sub(" ", segment)))
            if APPOINTMENT.search(segment):
                if re.search(r"\d", leftover):
                    return None
                continue
            if leftover or not ranges:
                return None
            for open_time, close_time in ranges:
                oh.add_days_range(day_list, open_time, close_time)

        return oh if oh.as_opening_hours() else None
