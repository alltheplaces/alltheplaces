import html
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_PT, OpeningHours, sanitise_day
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsPTSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "mcdonalds_pt"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.pt"]
    sitemap_urls = ["https://www.mcdonalds.pt/sitemap"]
    sitemap_rules = [("/restaurantes/", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = html.unescape(item.pop("name")).removeprefix("McDonald's ")
        self.clean_address(item)

        services = response.xpath("//div/@data-content").getall()
        apply_yes_no(Extras.DELIVERY, item, "McDelivery" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "McDrive" in services)
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in services)
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Fraldário" in services)
        apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in services)

        item["opening_hours"] = self.parse_opening_hours(
            response.xpath(
                '//div[contains(@class, "swiper-slide restaurantSchedule__service")][contains(., "Restaurante")]//li'
            )
        )
        item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(
            response.xpath(
                '//div[contains(@class, "swiper-slide restaurantSchedule__service")][contains(., "McDrive")]//li'
            )
        ).as_opening_hours()

        if "McCafé" in services:
            mccafe = item.deepcopy()
            mccafe["ref"] = "{}-mccafe".format(item["ref"])
            mccafe["brand"] = "McCafé"
            mccafe["brand_wikidata"] = "Q3114287"
            apply_category(Categories.CAFE, mccafe)
            yield mccafe

        apply_category(Categories.FAST_FOOD, item)
        yield item

    @staticmethod
    def clean_address(item: Feature) -> None:
        """Keep only the code in the postcode and take the town from the postal line.

        ``postalCode`` sometimes carries the postal town ("4560-264 Penafiel",
        "1900–806 Lisboa"), and ``addressLocality`` is often the restaurant's
        mall or street ("Norte Shopping"). ``addressRegion`` is the postal town
        shown after the postcode on the page ("4464-001 Senhora da Hora
        MATOSINHOS"), so it is the better city unless the street line itself
        ends with ", <locality>" ("Rua da Paz nºs/n, Cartaxo").
        """
        postal_town = None
        if match := POSTCODE.fullmatch((item.get("postcode") or "").strip()):
            code, extension, postal_town = match.groups()
            item["postcode"] = f"{code}-{extension}" if extension else code
            if postal_town and postal_town.isdigit():
                postal_town = None  # "1234 5678": a stray number, not a town
        locality = item.get("city")
        street_parts = (item.get("street_address") or "").rsplit(",", 1)
        if locality and len(street_parts) == 2 and street_parts[1].strip() == locality:
            return
        item["city"] = title_case_town(postal_town) or title_case_town(item.get("state")) or locality

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if day := sanitise_day(rule.xpath("cite/text()").get(), DAYS_PT):
                start_time, end_time = rule.xpath("span/text()").get().split(" às ")
                if end_time == "0h00":
                    end_time = "23h59"
                oh.add_range(day, start_time, end_time, time_format="%Hh%M")

        return oh


POSTCODE = re.compile(r"(\d{4})(?:\s*[-\u2010\u2011\u2013\u2014]\s*(\d{3}))?(?:\s+(.+))?")
LOWERCASE_PARTICLES = {"de", "da", "do", "das", "dos", "e"}


def title_case_town(value: str | None) -> str | None:
    """Return a town, unescaped and title-cased ("VILA NOVA DE GAIA"); None for "SÃO MIGUEL, AÇORES"."""
    value = html.unescape(value or "").strip()
    if not value or "," in value:
        return None
    if value.isupper():
        words = value.title().split()
        value = " ".join([words[0]] + [w.lower() if w.lower() in LOWERCASE_PARTICLES else w for w in words[1:]])
    return value
