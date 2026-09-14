import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_FR, OpeningHours
from locations.items import Feature

DAY_ALT = r"(?:Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)"
DAY_PHRASE_RE = re.compile(
    r"(?:Du\s+|Le\s+|La\s+)?" + DAY_ALT + r"(?:\s*,\s*" + DAY_ALT + r")*"
    r"(?:\s+et\s+(?:le\s+|la\s+)?" + DAY_ALT + r")?"
    r"(?:\s+au\s+" + DAY_ALT + r")?",
    re.IGNORECASE,
)
DAY_TOKEN_RE = re.compile(DAY_ALT, re.IGNORECASE)
TIME_PAIR_RE = re.compile(r"(\d{1,2})[h:](\d{2})?\s*(?:-|–|—|à|a)\s*(\d{1,2})[h:](\d{2})?", re.IGNORECASE)

COORD_RE = re.compile(r"!3d(-?[\d.]+)!4d(-?[\d.]+)")


def days_from_phrase(phrase: str) -> list[str]:
    tokens = DAY_TOKEN_RE.findall(phrase)
    en_days = [DAYS_FR[t.title()] for t in tokens]
    if re.search(r"\bau\b", phrase, re.IGNORECASE) and len(en_days) >= 2:
        si, ei = DAYS.index(en_days[0]), DAYS.index(en_days[-1])
        return DAYS[si : ei + 1] if si <= ei else DAYS[si:] + DAYS[: ei + 1]
    seen = []
    for d in en_days:
        if d not in seen:
            seen.append(d)
    return seen


def parse_opening_hours(raw: str) -> OpeningHours:
    oh = OpeningHours()
    if not raw:
        return oh
    text = raw.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    text = text.replace("\xa0", " ").replace("​", " ")
    text = re.sub(r"^\s*Horaires\s*:?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    matches = list(DAY_PHRASE_RE.finditer(text))
    if not matches:
        return oh
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(0), text[m.end() : end]))
    for day_phrase, rest in blocks:
        days = days_from_phrase(day_phrase)
        if not days:
            continue
        for h1, m1, h2, m2 in TIME_PAIR_RE.findall(rest):
            open_time = f"{int(h1):02d}:{m1 or '00'}"
            close_time = f"{int(h2):02d}:{m2 or '00'}"
            for day in days:
                oh.add_range(day, open_time, close_time)
    return oh


class GodotEtFilsFRSpider(Spider):
    name = "godot_et_fils_fr"
    item_attributes = {"brand": "Godot & Fils"}
    allowed_domains = ["godotetfils.com"]
    start_urls = ["https://godotetfils.com/agences-test/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    AJAX_URL = "https://godotetfils.com/wp-admin/admin-ajax.php"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_refs: set[str] = set()

    async def start(self) -> AsyncIterator[Any]:
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response: Response) -> Iterable[Any]:
        nonce_match = re.search(r'rechercheAgences\s*=\s*\{.*?"nonce":"([a-f0-9]+)"', response.text)
        if not nonce_match:
            self.logger.error("Could not find nonce on %s", response.url)
            return
        nonce = nonce_match.group(1)

        # Page 1 is server-rendered directly into the page.
        results_div = response.css("#resultats-agences")
        yield from self.parse_cards(results_div)

        page_numbers = {1}
        for data_page in response.css("[data-page]::attr(data-page)").getall():
            try:
                page_numbers.add(int(data_page))
            except ValueError:
                continue
        max_page = max(page_numbers)
        self.logger.info("Found %d total pages of agencies", max_page)

        for page in range(2, max_page + 1):
            yield FormRequest(
                self.AJAX_URL,
                formdata={
                    "action": "recherche_agences",
                    "nonce": nonce,
                    "search": "",
                    "paged": str(page),
                },
                callback=self.parse_ajax_page,
            )

    def parse_ajax_page(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_cards(response)

    def parse_cards(self, selector: Selector) -> Iterable[Feature]:
        for card in selector.css("[id^='agence-']"):
            ref = card.attrib.get("id", "").removeprefix("agence-")
            if not ref or ref in self.seen_refs:
                continue
            self.seen_refs.add(ref)

            name = card.css("h5.card-title::text").get("").strip()
            if not name:
                continue

            addr_full = self.field_text(card, "Adresse")
            hours_text = self.field_text(card, "Horaires")

            # The tel: href is sometimes malformed (e.g. "tel:%200519980720"), so
            # prefer the visible, human-formatted phone number text instead. A few
            # cards bundle more than one phone number/branch as literal text
            # (including a literal "<br>" artifact), so just clean that up.
            phone = card.css('a[href^="tel:"]::text').get("")
            phone = phone.replace("<br>", ", ")
            phone = re.sub(r"\s+", " ", phone).strip()
            phone = re.sub(r"(?:,\s*)+", ", ", phone).strip(", ")
            email = card.css('a[href^="mailto:"]::attr(href)').get("").removeprefix("mailto:").strip()
            website = card.css("a.btn-brand::attr(href)").get()

            item = Feature()
            item["ref"] = ref
            item["branch"] = name.removeprefix("GODOT & FILS ").strip()
            item["addr_full"] = addr_full
            item["phone"] = phone or None
            item["email"] = email or None
            item["website"] = website

            if "LAUSANNE" in name.upper():
                item["country"] = "CH"
            elif "LUXEMBOURG" in name.upper():
                item["country"] = "LU"
            else:
                item["country"] = "FR"

            maps_href = card.xpath('.//p[contains(., "Adresse")]//a/@href').get()
            if maps_href:
                if m := COORD_RE.search(maps_href):
                    item["lat"] = m.group(1)
                    item["lon"] = m.group(2)

            if hours_text:
                item["opening_hours"] = parse_opening_hours(hours_text)

            apply_category(Categories.SHOP_GOLD_BUYER, item)

            yield item

    @staticmethod
    def field_text(card: Selector, label: str) -> str:
        p = card.xpath(f'.//p[contains(., "{label} :")]')
        if not p:
            return ""
        texts = p.css("::text").getall()
        joined = " ".join(t.strip() for t in texts if t.strip())
        joined = re.sub(rf"^{re.escape(label)}\s*:\s*", "", joined).strip()
        return joined
