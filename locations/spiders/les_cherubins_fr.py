import html
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours, day_range
from locations.items import Feature


class LesCherubinsFRSpider(Spider):
    name = "les_cherubins_fr"
    item_attributes = {"brand": "Les Chérubins", "brand_wikidata": "Q141220403"}
    # JSON feed backing the Leaflet map on https://www.les-cherubins.com/creches/index.html
    start_urls = ["https://www.les-cherubins.com/global/includes/ajax/gmap-creches.php"]

    def parse(self, response: Response) -> Iterable[Feature | Request]:
        for place in response.json()["places"]:
            # "icone_creche_vert" flags an open crèche; "icone_creche_violet" is "opening soon"
            # and "icone_enquete" is a prospective project with only a survey form.
            if place.get("icone") != "icone_creche_vert":
                continue

            parts = [html.unescape(p).strip() for p in place["texte"].split("<br />")]

            item = Feature()
            item["branch"] = re.sub(r"^Micro[- ]crèche\s+", "", place["name_simple"], flags=re.IGNORECASE)
            item["street_address"] = parts[0]
            item["lat"], item["lon"] = (coord.strip() for coord in place["gmap"].split(","))

            if len(parts) >= 2 and re.match(r"\d{5} - ", parts[1]):
                item["postcode"], item["city"] = parts[1].split(" - ", 1)
            else:
                item["city"] = place["ville"]

            apply_category(Categories.CHILD_CARE, item)

            if website := re.search(r"https://[\w.-]+\.les-cherubins-creches\.com", place["texte"]):
                item["website"] = website.group(0)
                item["ref"] = website.group(0).split("//", 1)[1].split(".", 1)[0]
                yield response.follow(item["website"], callback=self.parse_creche, cb_kwargs={"item": item})
            else:
                item["ref"] = "-".join(filter(None, [item.get("postcode"), item["branch"]]))
                yield item

    def parse_creche(self, response: Response, item: Feature) -> Iterable[Feature]:
        # A handful of crèche subdomains are not live yet and 302 to the generic listing page.
        if "les-cherubins-creches.com" in response.url:
            if phone := response.xpath('//a[starts-with(@href, "tel:")]/@href').get():
                # Some pages list two numbers separated by "/" or " - ".
                phone = re.split(r"/| - ", phone.removeprefix("tel:"))[0]
                item["phone"] = re.sub(r"\s+", " ", phone).strip()
            mailto = response.xpath('//a[starts-with(@href, "mailto:")]/@href').get("")
            if email := re.search(r"[-\w.+]+@[-\w]+\.[-\w.]+", mailto):
                item["email"] = email.group(0)
            item["opening_hours"] = self.parse_hours(response)
        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        # Each row is "<strong>Lundi :</strong> 07:30 - 18:30", with combined labels such as
        # "Samedi et Dimanche : Fermé".
        for row in response.xpath('//div[contains(@class, "horaire")]//p'):
            label = (row.xpath("string(strong)").get() or "").strip().rstrip(":").strip()
            value = " ".join(row.xpath("text()").getall()).strip()
            if not (days := self.expand_days(label)) or not value:
                continue
            if value.lower() in CLOSED_FR:
                oh.set_closed(days)
                continue
            if "-" not in value:
                continue
            start, end = (self.clean_time(t) for t in value.split("-", 1))
            if not (start and end):
                continue
            for day in days:
                oh.add_range(day, start, end)
        return oh

    @staticmethod
    def expand_days(label: str) -> list[str]:
        if " au " in label:
            start, end = (DAYS_FR.get(part.strip()) for part in label.split(" au ", 1))
            return day_range(start, end) if start and end else []
        return [day for part in label.split(" et ") if (day := DAYS_FR.get(part.strip()))]

    @staticmethod
    def clean_time(value: str) -> str | None:
        # Times come as "07:30", "18", "8H" or "18h30".
        hour, _, minute = value.strip().lower().replace("h", ":").partition(":")
        if not hour.strip().isdigit():
            return None
        return f"{int(hour):02d}:{(minute.strip() or '00').zfill(2)}"
