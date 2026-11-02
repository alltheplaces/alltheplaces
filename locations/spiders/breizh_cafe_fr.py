import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BreizhCafeFRSpider(SitemapSpider):
    name = "breizh_cafe_fr"
    item_attributes = {"brand": "Breizh Café", "brand_wikidata": "Q141342904"}
    sitemap_urls = ["https://www.breizhcafe.com/sitemap.xml"]
    # The shop, guest rooms, gallery and farm pages also mention the brand but are not restaurants.
    skipped_names = ["CHAMBRES", "GALERIE", "FERME", "ÉPICERIE"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        lines = [
            line.strip()
            for text in response.xpath("//main//text()[not(ancestor::script) and not(ancestor::style)]").getall()
            for line in text.splitlines()
            if line.strip()
        ]
        if "PLAN" not in lines:
            return
        plan = lines.index("PLAN")

        # The info block reads: name lines, address, phone, "PLAN", then the opening hours.
        index = plan - 1
        phone = None
        if re.fullmatch(r"[\d ]{10,14}", lines[index]):
            phone = lines[index]
            index -= 1
        address = lines[index]
        if not (match := re.fullmatch(r"(.+?),?\s+(\d{5})\s+(.+)", address)):
            return
        name_lines = []
        index -= 1
        while (
            index >= 0
            and not re.search(r"\d{5}", lines[index])
            and lines[index].upper() not in ("RÉSERVER", "DÉCOUVRIR")
        ):
            name_lines.insert(0, lines[index])
            index -= 1
        name = " ".join(name_lines).upper()
        if "BREIZH CAF" not in name or any(word in name for word in self.skipped_names):
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[1]
        item["website"] = response.url
        item["street_address"] = clean_address(match.group(1))
        item["postcode"] = match.group(2)
        item["city"] = match.group(3).title()
        item["phone"] = phone

        name = re.sub(r"BREIZH CAF[EÉ]", "Breizh Café", name)
        if name.startswith("Breizh Café "):
            item["branch"] = name.removeprefix("Breizh Café ").title().replace(" De ", " de ")
        else:
            item["name"] = name.title()

        for link in response.xpath('//a[contains(@href, "google.") and contains(@href, "/maps/")]/@href').getall():
            if coords := re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", link):
                item["lat"], item["lon"] = coords.groups()
                break

        item["opening_hours"] = self.parse_hours(lines[plan + 1 :])

        if "BAR À CIDRES" in name.upper():
            apply_category(Categories.BAR, item)
        else:
            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "crepe"

        yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours:
        oh = OpeningHours()
        days = []
        for line in lines:
            times = re.findall(r"(\d{1,2})[hH](\d{2})?\s*(?:-|à)\s*(\d{1,2})[hH](\d{2})?", line)
            if times:
                for start_hour, start_minute, end_hour, end_minute in times:
                    oh.add_days_range(
                        days,
                        "{}:{}".format(start_hour, start_minute or "00"),
                        "{}:{}".format(end_hour, end_minute or "00"),
                    )
            elif line.lower() in ("fermé", "ferme"):
                oh.set_closed(days)
            elif day_list := BreizhCafeFRSpider.parse_days(line.rstrip(" :")):
                days = day_list
            else:
                break
        return oh

    @staticmethod
    def parse_days(text: str) -> list[str]:
        days = []
        for part in text.split(","):
            names = [name.strip() for name in part.split("-")]
            parsed = [sanitise_day(name[:3].title(), DAYS_FR) for name in names if name]
            if not parsed or None in parsed:
                return []
            if len(parsed) == 2:
                start, end = parsed
                all_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
                days.extend(all_days[all_days.index(start) : all_days.index(end) + 1])
            else:
                days.extend(parsed)
        return days
