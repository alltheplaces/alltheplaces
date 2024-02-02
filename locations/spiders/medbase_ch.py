import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, DAYS_FR, OpeningHours, day_range
from locations.items import Feature


class MedbaseCHSpider(scrapy.Spider):
    name = "medbase_ch"
    allowed_domains = ["medbase.ch"]
    start_urls = ["https://www.medbase.ch/standorte"]

    def parse(self, response):
        for tr in response.css("tr.location"):
            feature = Feature(
                brand="Medbase",
                brand_wikidata="Q50038690",
                extras={},
                lat=float(tr.xpath("@data-lat").get()),
                lon=float(tr.xpath("@data-lng").get()),
                name="Medbase",
                ref=tr.xpath("@data-uid").get(),
            )
            apply_category(Categories.DOCTOR_GP, feature)
            self.parse_address(tr, feature)
            self.parse_branch(tr, feature)
            self.parse_email(tr, feature)
            self.parse_opening_hours(tr, feature)
            self.parse_website(response, tr, feature)
            yield feature

    def parse_address(self, tr, feature):
        lines = tr.css("div.left").xpath("p/text()").extract()
        lines = list(filter(None, [" ".join(x.split()) for x in lines]))
        feature["country"] = "CH"
        feature["street_address"] = lines[0]
        if m := re.match(r"^(\d{4})\s+(.+)$", lines[1]):
            feature["postcode"] = m.group(1)
            feature["city"] = m.group(2)
        for line in lines:
            if line.startswith("Tel."):
                feature["phone"] = line.removeprefix("Tel.")
            elif line.startswith("Fax "):
                feature["extras"]["fax"] = line.removeprefix("Fax ")

    def parse_branch(self, tr, feature):
        branch = tr.css(".title").xpath("text()").get()
        branch = branch.removeprefix("Medbase")
        feature["branch"] = " ".join(branch.split())

    def parse_email(self, tr, feature):
        if m := re.search(r"mailto:([a-zA-Z0-9\-]+@medbase\.ch)", tr.get()):
            feature["email"] = m.group(1)

    def parse_opening_hours(self, tr, feature):
        oh = OpeningHours()
        lines = tr.css(".telephoneHours").xpath("*/text()").getall()
        lines = [line.strip() for line in lines]
        for sep in ["", "Physiotherapie"]:
            if sep in lines:
                lines = lines[: lines.index(sep)]
        for line in lines:
            for prefix in ["Walk-in:", "Sprechstunden:"]:
                line = line.removeprefix(prefix)
            if m := re.match(r"^\s*(\D+)\s+(\d.+)", line):
                for day in self.parse_days(m.group(1)):
                    for open_time, close_time in self.parse_hours(m.group(2)):
                        oh.add_range(day, open_time, close_time)
        feature["opening_hours"] = oh.as_opening_hours()

    def parse_days(self, days):
        result = set()
        for d in re.split(r"[,/]|und|et", days):
            d = d.strip()
            if m := re.match(r"^([A-Z][a-z])\s*[—–\-]\s*([A-Z][a-z])$", d):
                d1, d2 = m.groups()
                if d1 in DAYS_DE and d2 in DAYS_DE:
                    for day in day_range(DAYS_DE[d1], DAYS_DE[d2]):
                        result.add(day)
                elif d1 in DAYS_FR and d2 in DAYS_FR:
                    for day in day_range(DAYS_FR[d1], DAYS_FR[d2]):
                        result.add(day)
            elif day := DAYS_DE.get(d) or DAYS_FR.get(d):
                result.add(day)
        return result

    def parse_hours(self, hours):
        result = []
        for h in re.split(r"[,/]|und|et", hours):
            if m := re.search(r"^(\d\d\.\d\d)\s*[—–\-]\s*(\d\d\.\d\d)", h.strip()):
                result.append(tuple([h.replace(".", ":") for h in m.groups()]))
        return result

    def parse_website(self, response, tr, feature):
        if urls := tr.xpath("*/a/@href").extract():
            feature["website"] = response.urljoin(urls[0])
