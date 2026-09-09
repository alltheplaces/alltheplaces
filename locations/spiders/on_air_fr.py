import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class OnAirFRSpider(SitemapSpider):
    name = "on_air_fr"
    item_attributes = {"brand": "On Air", "brand_wikidata": "Q138313370"}
    sitemap_urls = ["https://onair-fitness.fr/club-sitemap.xml"]
    sitemap_rules = [(r"/club/[^/]+/$", "parse")]

    DAY_GROUPS = {
        "du lundi au vendredi": DAYS_WEEKDAY,
        "du lundi au samedi": DAYS[:-1],
        "du lundi au dimanche": DAYS,
        "le week-end": DAYS_WEEKEND,
        "7j/7": DAYS,
    }
    HOURS_RE = re.compile(
        r"(?P<days>7j/7|du lundi au (?:vendredi|samedi|dimanche)|le week-end)"
        r"\s+de\s+(?P<open>\d{1,2}h(?:\d{2})?)\s+(?:à|a)\s+(?P<close>\d{1,2}h(?:\d{2})?)",
        re.IGNORECASE,
    )

    def parse(self, response: Response, **kwargs: Any):
        item = Feature(**self.item_attributes)
        item["ref"] = item["website"] = response.url
        item["branch"] = self.parse_branch(response)
        item["country"] = "FR"
        item["phone"] = (
            re.sub(r"\s+", "", response.css(".single_span_icn.tel").xpath("normalize-space()").get("")) or None
        )
        item["email"] = response.css(".single_span_icn.mail a::attr(href)").get("").removeprefix("mailto:") or None

        map_link = response.css(".single_span_icn.map a")
        self.parse_address(item, map_link.css("::text").getall())

        if hours_text := " ".join(response.css(".single_span_icn.horaires::text").getall()):
            item["opening_hours"] = self.parse_opening_hours(hours_text)

        extract_google_position(item, response)
        apply_category(Categories.GYM, item)

        yield item

    @staticmethod
    def parse_branch(response: Response) -> str:
        name = " ".join(response.css("h1::text").getall())
        return re.sub(r"\s+", " ", name).removeprefix("ON AIR SALLE DE SPORT ").strip().title()

    @staticmethod
    def parse_address(item: Feature, address_text: list[str]) -> None:
        lines = [line.strip() for text in address_text for line in text.splitlines() if line.strip()]
        if not lines:
            return

        postcode_city = re.fullmatch(r"(?P<postcode>\d{5})\s+(?P<city>.+)", lines[-1])
        if postcode_city:
            item["street_address"] = clean_address(lines[:-1])
            item["postcode"] = postcode_city.group("postcode")
            item["city"] = postcode_city.group("city")
        else:
            item["addr_full"] = clean_address(lines)

    @classmethod
    def parse_opening_hours(cls, hours_text: str) -> OpeningHours | str:
        hours_text = cls.normalise_hours_text(hours_text)
        if "7j/7" in hours_text and "24h/24" in hours_text:
            return "24/7"

        opening_hours = OpeningHours()
        for match in cls.HOURS_RE.finditer(hours_text.lower()):
            open_time = cls.normalise_time(match.group("open"))
            close_time = cls.normalise_time(match.group("close"))
            for day in cls.DAY_GROUPS[match.group("days")]:
                opening_hours.add_range(day, open_time, close_time)
        return opening_hours

    @staticmethod
    def normalise_time(value: str) -> str:
        hour, minute = value.split("h", maxsplit=1)
        return f"{int(hour):02d}:{minute or '00'}"

    @staticmethod
    def normalise_hours_text(hours_text: str) -> str:
        text = hours_text.lower().replace("weekend", "week-end").replace("minuit", "00h")
        text = re.sub(r"lundi\s*-\s*dimanche\s*:", "du lundi au dimanche de", text)
        text = re.sub(
            r"(?P<days>du lundi au (?:vendredi|samedi|dimanche)|le week-end)\s*:",
            r"\g<days> de",
            text,
        )
        text = re.sub(r"(?<=\d)h\s*-\s*(?=\d)", "h à ", text)
        if re.fullmatch(r"\s*\d{1,2}h(?:\d{2})?\s+à\s+\d{1,2}h(?:\d{2})?\s*", text):
            return "7j/7 de " + text
        return text
