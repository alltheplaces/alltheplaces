import re
from typing import Any, AsyncIterator, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.selector import Selector
from scrapy.utils.sitemap import Sitemap

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

SITEMAP_INDEX = "https://www.elephantbleu.com/sitemap_index.xml"
LOCATORS = {
    "FR": "https://www.elephantbleu.com/ma-station-de-lavage/",
    "CH": "https://www.elephantbleu.com/fr-ch/ma-station-de-lavage/",
}
SERVICES = {
    "Aspirateur": Extras.VACUUM_CLEANER,
    "Gonfleur": Extras.COMPRESSED_AIR,
    "Paiement application mobile": PaymentMethods.APP,
    "CB sans contact sur les pistes haute-pression": PaymentMethods.CONTACTLESS,
    "CB sans contact sur les aspirateurs": PaymentMethods.CONTACTLESS,
}

# Last group of digits of the right length: some addresses end with "(853)".
POSTCODE = {"FR": re.compile(r"\b(\d{5})\b(?!.*\b\d{5}\b)"), "CH": re.compile(r"\b(\d{4})\b(?!.*\b\d{4}\b)")}

# Hours are franchisee-written free text. Read: "24h/24", a single daily range, or clauses like
# "7h-21h du lu-sa, 9h-13h dimanche et jours fériés"; skip anything else, and any text giving a
# facility (gantry, high-pressure bays) or a season its own hours.
SKIP_HOURS = re.compile(r"portique|pression|rouleau|sécheresse|avril", re.IGNORECASE)
DAY_WORDS = re.compile(
    r"\b(?:lu|lundi|ma|mardi|me|mercredi|je|jeudi|ve|vendredi|sa|samedi|di|dimanches?|ferm\w*)\b", re.IGNORECASE
)
DAY_SPAN = re.compile(
    r"\b(?:(lundi au dimanche)|(lu\s*-\s*sa|lundi au samedi)|(lu\s*-\s*ve)|(sa)|(dimanches?))\b", re.IGNORECASE
)
DAY_SPAN_DAYS = [DAYS, DAYS[:6], DAYS[:5], ["Sa"], ["Su"]]
ALWAYS_OPEN = re.compile(r"24\s*h?\s*(?:00)?\s*(?:/|sur)?\s*24|non\s*stop", re.IGNORECASE)
TIME_RANGE = re.compile(r"(\d{1,2})\s*[h:]\s*(\d{2})?\s*(?:-|/|à|a)?\s*(\d{1,2})\s*[h:]\s*(\d{2})?", re.IGNORECASE)


class ElephantBleuSpider(Spider):
    name = "elephant_bleu"
    item_attributes = {"brand": "Éléphant Bleu", "brand_wikidata": "Q3144358", "name": "Éléphant Bleu"}
    allowed_domains = ["www.elephantbleu.com"]

    async def start(self) -> AsyncIterator[Request]:
        # Sitemap dates only break ties between duplicate listings, so a missing sitemap isn't fatal.
        lastmod = {}
        for url in await self.fetch_sitemap(SITEMAP_INDEX):
            if "/center-sitemap" in url:
                lastmod.update(await self.fetch_sitemap(url))
        for country, url in LOCATORS.items():
            yield Request(url, cb_kwargs={"country": country, "lastmod": lastmod})

    async def fetch_sitemap(self, url: str) -> dict[str, str]:
        response = await self.crawler.engine.download_async(Request(url))
        if response.status != 200:
            self.logger.warning(f"Sitemap {url} returned HTTP {response.status}")
            return {}
        return {entry["loc"]: entry.get("lastmod", "") for entry in Sitemap(response.body) if "loc" in entry}

    def parse(self, response: Response, country: str, lastmod: dict[str, str], **kwargs: Any) -> Iterable[Feature]:
        # The map markers have coordinates and hours, the card list has the correct page links
        # and service labels; both list the same centres in the same order.
        markers = chompjs.parse_js_object(re.split(r"\bBLOCK_MAP\s*=", response.text, maxsplit=1)[1])["markers"]
        cards = response.css("#centers-container a.card-center")
        if len(markers) != len(cards):
            raise ValueError(f"{len(markers)} map markers but {len(cards)} centre cards")

        places = {}
        for marker, card in zip(markers, cards):
            popup = Selector(text=marker["popmap"])
            address, *other_lines = popup.css("div.mb-2 p").xpath("normalize-space()").getall() or [""]
            card_address = card.css(".card-center__address").xpath("normalize-space()").get("")
            if address.casefold() != card_address.casefold():
                self.logger.warning(f"Map marker and centre card disagree: {address!r} vs {card_address!r}")
                continue

            item = Feature()
            item["ref"] = card.attrib["href"].rstrip("/").rsplit("/", 1)[-1]
            item["website"] = response.urljoin(item["ref"] + "/")
            item["lat"] = marker["lat"]
            item["lon"] = marker["lng"]
            item["branch"] = popup.css("p.h3__lightb::text").get("").strip()

            item["addr_full"] = address
            item["country"] = country
            if match := re.search(r"\bB-(\d{4})\b", address) or POSTCODE[country].search(address):
                item["postcode"] = match.group(1)
                item["street_address"] = address[: match.start()].strip(" ,-")
                item["city"] = address[match.end() :].strip(" ,-")
                if match.group().startswith("B-"):
                    item["country"] = "BE"
                elif item["postcode"].startswith("974"):
                    item["country"] = "RE"

            if other_lines:
                item["opening_hours"] = self.parse_hours(" ".join(other_lines))

            for label in card.css("p.center__text::text").getall():
                if attribute := SERVICES.get(label.strip()):
                    apply_yes_no(attribute, item, True)
            apply_category(Categories.CAR_WASH, item)

            # A few centres are listed twice under different slugs, which the pipeline's ref dedup
            # can't catch; keep the most recently updated page.
            key = (address.casefold(), item["lat"], item["lon"])
            kept = places.get(key)
            if kept is None or lastmod.get(item["website"], "") > lastmod.get(kept["website"], ""):
                places[key] = item
        yield from places.values()

    def parse_hours(self, hours: str) -> OpeningHours | None:
        if SKIP_HOURS.search(hours):
            return None
        # "y compris les dimanches", "dimanches et jours fériés compris" only confirm the daily hours.
        hours = re.sub(r"\by compris[^,.]*|,[^,.]*\bcompris\b", "", hours)
        oh = OpeningHours()
        if not DAY_WORDS.search(hours):
            if ALWAYS_OPEN.search(hours):
                oh.add_days_range(DAYS, "00:00", "23:59")
            elif len(ranges := TIME_RANGE.findall(hours)) == 1:
                oh.add_days_range(DAYS, *self.to_times(ranges[0]))
            return oh or None

        for clause in re.split(r",|\s/\s|\bet\b", hours):
            ranges = TIME_RANGE.findall(clause)
            days = [DAY_SPAN_DAYS[i] for m in DAY_SPAN.finditer(clause) for i, group in enumerate(m.groups()) if group]
            closed = "ferm" in clause.lower()
            if len(ranges) == 1 and len(days) == 1 and not closed:
                oh.add_days_range(days[0], *self.to_times(ranges[0]))
            elif not ranges and len(days) == 1 and closed:
                oh.set_closed(days[0])
            elif ranges or days:
                return None
        return oh or None

    @staticmethod
    def to_times(time_range: tuple[str, str, str, str]) -> tuple[str, str]:
        start_h, start_m, end_h, end_m = time_range
        return f"{int(start_h):02}:{start_m or '00'}", f"{int(end_h):02}:{end_m or '00'}"
