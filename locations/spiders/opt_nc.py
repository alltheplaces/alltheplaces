import json
import re
from typing import Any

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAYS_NC = {
    "lundi": "Mo",
    "mardi": "Tu",
    "mercredi": "We",
    "jeudi": "Th",
    "vendredi": "Fr",
    "samedi": "Sa",
    "dimanche": "Su",
}


class OptNCSpider(Spider):
    name = "opt_nc"
    item_attributes = {
        "operator": "Office des postes et télécommunications de Nouvelle-Calédonie",
        "operator_wikidata": "Q3349600",
    }
    allowed_domains = ["office.opt.nc"]
    # The agency map embeds every agency in drupalSettings; details (address, phone, hours) come
    # from the HTML fragment the map loads when a marker is clicked.
    start_urls = ["https://office.opt.nc/fr/carte-du-reseau-d-agences"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        settings = json.loads(response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get())
        for district, agencies in settings["opt_maps_agency"]["agencies"].items():
            for agency in agencies:
                if agency.get("hiddenOptNc") or not agency.get("position"):
                    continue
                name = agency["designation"].strip()
                # Not public counters: the business-customers agency and the mail sorting/delivery centres.
                if not name.lower().startswith("agence de "):
                    continue
                item = Feature()
                item["ref"] = str(agency["id"])
                item["branch"] = name[len("Agence de ") :].strip()
                item["lat"], item["lon"] = agency["position"]["lat"], agency["position"]["lon"]
                item["city"] = district.title()
                item["country"] = "NC"
                yield Request(
                    f"https://office.opt.nc/fr/opt/maps/agency?id={agency['id']}",
                    callback=self.parse_agency,
                    cb_kwargs={"item": item},
                )

    def parse_agency(self, response: Response, item: Feature) -> Any:
        details = Selector(text=response.json()["html"])
        lines = [t.strip() for t in details.css(".agency-address div ::text").getall() if t.strip()]
        if lines:
            if m := re.fullmatch(r"(988\d\d)\s*(.*)", lines[-1]):
                item["postcode"] = m.group(1)
                if m.group(2):
                    item["city"] = m.group(2).title()
                lines = lines[:-1]
            item["street_address"] = ", ".join(lines)
        for contact in details.css(".agency-contacts div"):
            text = " ".join(t.strip() for t in contact.css("::text").getall() if t.strip())
            if "@" in text:
                item["email"] = text
            elif re.fullmatch(r"[\d ]{6,}", text):
                item["phone"] = text
        item["opening_hours"] = self.parse_hours(details.css(".schedule div ::text").getall())
        apply_category(Categories.POST_OFFICE, item)
        yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours:
        # "Du lundi au mercredi de 07:45 à 15:30", "Le jeudi de 07:45 à 11:30 et de 12:15 à 14:00"
        oh = OpeningHours()
        for line in lines:
            names = [DAYS_NC[d] for d in re.findall(r"\b(" + "|".join(DAYS_NC) + r")\b", line.lower())]
            if not names:
                continue
            if len(names) == 2 and re.search(r"\bau\b", line):
                days = DAYS[DAYS.index(names[0]) : DAYS.index(names[1]) + 1]
            else:
                days = names
            for start, end in re.findall(r"(\d{1,2}[:h]\d{2})\s*à\s*(\d{1,2}[:h]\d{2})", line):
                oh.add_days_range(days, start.replace("h", ":").zfill(5), end.replace("h", ":").zfill(5))
        return oh
