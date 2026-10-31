import logging
import re
import urllib.parse
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FI, OpeningHours
from locations.items import Feature

logger = logging.getLogger(__name__)


class MuseotFISpider(SitemapSpider):
    name = "museot_fi"
    allowed_domains = ["museot.fi"]
    sitemap_urls = ["https://museot.fi/mod_google_sitemap/museot.php"]
    sitemap_rules = [(r"/fi/museot/", "parse_museum")]

    COORD_RE = re.compile(r"::\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)")
    POSTCODE_RE = re.compile(r"(\d{5})\s+([^0-9,;(.]+)")
    BARE_POSTCODE_RE = re.compile(r",\s*(\d{5})\s*,")
    PHONE_RE = re.compile(r"[+\d(][\d\s\-()/]*\d")
    HOURS_RE = re.compile(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$")
    AT_EMAIL_RE = re.compile(r"[\w.+-]+\(at\)[\w.-]+\.[A-Za-z]{2,}")
    STREET_SUFFIX_RE = re.compile(r"(katu|tie|kuja|polku|raitti|väylä)$", re.IGNORECASE)
    # Empty-filename upstream placeholder shared by 50 pages without a photo.
    PLACEHOLDER_IMAGE = "https://museot.fi/uploadkuvat/-"

    # Source-labelled Museo records whose described primary function is not
    # a museum: a working church, an events venue, an Aalto town hall and an
    # immersive entertainment venue (attractions), three botanical gardens,
    # two visitor centres and three exhibition halls without collections.
    NON_MUSEUM_CATEGORIES = {
        "temppeliaukion-kirkko": Categories.PLACE_OF_WORSHIP,
        "finlandia-talo": Categories.EVENTS_VENUE,
        "saynatsalon-kunnantalo": Categories.TOURISM_ATTRACTION,
        "elamystila-visio": Categories.TOURISM_ATTRACTION,
        "luomus-kaisaniemen-kasvitieteellinen-puutarha": Categories.LEISURE_GARDEN,
        "luomus-kumpulan-kasvitieteellinen-puutarha": Categories.LEISURE_GARDEN,
        "turun-yliopiston-kasvitieteellinen-puutarha": Categories.LEISURE_GARDEN,
        "bomarsundin-vierailukeskus": Categories.TOURISM_INFORMATION,
        "saaristokeskus-korpostrom": Categories.TOURISM_INFORMATION,
        "helsingin-taidehalli": Categories.TOURISM_GALLERY,
        "seinajoen-taidehalli": Categories.TOURISM_GALLERY,
        "wasa-graffitilandia": Categories.TOURISM_GALLERY,
    }
    # Recurring biennale event and guided-tour product, not POIs; homes are
    # the event listings and the ahlstrom-ruukki museum record respectively.
    NON_MUSEUM_DROPS = {"fiskars-village-art-design-biennale", "ahlstrom-ruukki-ruukkikierrokset"}

    # Formal per-museum accessibility/service criteria as topic-link ids
    # (1:1 with labels across all pages): full and partial step-free
    # access, accessible wc, dogs allowed.
    ACCESS_FULL_ID = "33"
    ACCESS_PARTIAL_ID = "38"
    ACCESS_WC_ID = "19"
    DOG_ID = "217"
    KNOWN_ACCESS_IDS = frozenset(
        {
            "9",
            "10",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "33",
            "34",
            "35",
            "36",
            "37",
            "38",
            "46",
            "93",
            "94",
            "95",
            "96",
            "97",
            "98",
            "99",
            "137",
            "217",
            "225",
        }
    )

    def _stat(self, key: str) -> None:
        try:
            stats = self.crawler.stats
        except AttributeError:
            return
        if stats is not None:
            stats.inc_value(key)

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/fi/museot/" in entry["loc"]:
                yield entry
            else:
                self._stat("atp/museot_fi/dropped/sitemap_lang")

    def closed(self, reason: str) -> None:
        # A sitemap or format change yielding zero fi entries must log
        # loudly instead of looking like a clean empty run.
        try:
            count = self.crawler.stats.get_value("item_scraped_count", 0)
        except AttributeError:
            return
        if reason == "finished" and not count:
            logger.error("museot_fi: finished with zero items scraped")

    def parse_museum(self, response: Response) -> Iterable[Feature]:
        slug = response.url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
        name = response.xpath("//div[contains(@class, 'mus_sisalto')]//h1/span/text()").get()
        if not name or not name.strip():
            self._stat("atp/museot_fi/dropped/no_name")
            return
        item = Feature()
        item["ref"] = slug
        item["name"] = name.strip()
        if slug in self.NON_MUSEUM_DROPS:
            self._stat(f"atp/museot_fi/dropped/not_a_museum/{slug}")
            return
        if website := response.xpath(
            "//div[@class='museon_tiedot']//a[contains(text(), 'Museon kotisivut')]/@href"
        ).get():
            item["website"] = website.strip()
        else:
            self._stat("atp/museot_fi/empty/website")
        if coords := self.parse_coords(response):
            item["lat"], item["lon"] = coords
        raw_addr = response.xpath("//p[@class='paikka']/text()").getall()
        street, city, postcode = self.parse_address(" ".join(raw_addr))
        if street:
            item["street_address"] = street
        else:
            self._stat("atp/museot_fi/empty/street_address")
        if city:
            item["city"] = city
        else:
            self._stat("atp/museot_fi/empty/city")
        if postcode:
            item["postcode"] = postcode
        else:
            self._stat("atp/museot_fi/empty/postcode")
        if phone := self.parse_phone(response):
            item["phone"] = phone
        else:
            self._stat("atp/museot_fi/empty/phone")
        if email := response.xpath("//div[@class='lisatiedot']//a[starts-with(@href, 'mailto:')]/@href").get():
            # Some hrefs carry trailing sentence punctuation (".", ",")
            # inside the quotes, an upstream typo.
            item["email"] = email.split(":", 1)[1].strip().rstrip(".,")
        elif at_mail := response.xpath("//div[@class='lisatiedot']//text()").re_first(self.AT_EMAIL_RE.pattern):
            # Anti-spam "(at)" booking contacts decode to the same address.
            item["email"] = at_mail.replace("(at)", "@")
            self._stat("atp/museot_fi/email/deobfuscated")
        else:
            self._stat("atp/museot_fi/empty/email")
        if hours := self.parse_hours(response):
            item["opening_hours"] = hours
        if image := (response.xpath("//meta[@property='og:image']/@content").get() or "").strip():
            if image == self.PLACEHOLDER_IMAGE:
                self._stat("atp/museot_fi/dropped/placeholder_image")
            else:
                item["image"] = image
        else:
            self._stat("atp/museot_fi/empty/image")
        self.apply_accessibility(item, response)
        apply_category(self.NON_MUSEUM_CATEGORIES.get(slug, Categories.MUSEUM), item)
        yield item

    def apply_accessibility(self, item: Feature, response: Response) -> None:
        # Topic ids from the accessibility/service blocks only (theme links
        # use topic ids too, so a page-wide collection would overmatch).
        # Partial step-free access is the narrower claim and wins over full.
        ids = set()
        for box in response.xpath("//div[@class='lisatiedot'][h2[@class='esteettomyys' or @class='palvelut']]"):
            ids.update(box.xpath(".//a/@href").re(r"topic_(\d+)"))
        for tid in sorted(ids - self.KNOWN_ACCESS_IDS):
            self._stat(f"atp/museot_fi/access/unmapped_topic/{tid}")
        if self.ACCESS_PARTIAL_ID in ids:
            apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, True)
        elif self.ACCESS_FULL_ID in ids:
            apply_yes_no(Extras.WHEELCHAIR, item, True)
        if self.ACCESS_WC_ID in ids:
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, True)
        if self.DOG_ID in ids:
            apply_yes_no(Extras.DOG, item, True)

    def parse_coords(self, response: Response) -> tuple | None:
        raw = response.xpath("//input[@id='mh_osoite2']/@value").get()
        if not raw:
            self._stat("atp/museot_fi/empty/coords")
            return None
        match = self.COORD_RE.search(urllib.parse.unquote(raw))
        if not match:
            self._stat("atp/museot_fi/dropped/bad_coords")
            return None
        lat, lon = float(match.group(1)), float(match.group(2))
        if not (59 <= lat <= 71 and 19 <= lon <= 32):
            self._stat("atp/museot_fi/dropped/bad_coords")
            return None
        return lat, lon

    @staticmethod
    def _clean_city(raw: str | None) -> str | None:
        # Postal-locality cleanup: bilingual concatenations ("Hämeenlinna
        # Tavastehus") and district tails reduce to the first token, keeping
        # two-letter province qualifiers ("Koski Tl"); the postcode label
        # "Oulun kaupunki" maps to the municipality Oulu.
        if not raw:
            return None
        city = raw.strip()
        if city == "Oulun kaupunki":
            return "Oulu"
        head, _, tail = city.partition(" ")
        if not tail or (len(tail) <= 2 and tail[0].isupper()):
            return city
        return head

    @staticmethod
    def parse_address(raw: str) -> tuple:
        # Freeform Finnish address lines in many shapes: standard
        # "Street 7, 40600 City", "Street 7, City", street-only, venue
        # prefixes ("Venue, Street 7, City"), bilingual repeats joined by
        # ";" (fi part wins; first postcode wins otherwise), ", POSTCODE,"
        # middles and trailing parking notes after the postcode-city tail
        # (dropped).
        text = " ".join(raw.split())
        if not text:
            return None, None, None
        text = text.split(";")[0]
        text = re.split(r",\s*Pysäköinti", text)[0]
        text = MuseotFISpider.BARE_POSTCODE_RE.sub(r", \1 ", text)
        if match := MuseotFISpider.POSTCODE_RE.search(text):
            street = text[: match.start()].strip(" ,")
            parts = [p.strip() for p in street.split(",") if p.strip() and not re.fullmatch(r"\d{5}", p.strip())]
            return (", ".join(parts) or None, MuseotFISpider._clean_city(match.group(2)), match.group(1))
        if match := re.search(r"(\d{5})\s*$", text):
            return text[: match.start()].strip(" ,") or None, None, match.group(1)
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) >= 2 and not re.search(r"\d", parts[-1]):
            # Buildings ("Kehräämö (Kirjastotalo)", "T/D -rakennus") are
            # not municipalities; numberless streets split on suffix.
            if "(" in parts[-1] or "rakennus" in parts[-1].lower():
                return text, None, None
            if any(re.search(r"\d", p) for p in parts[:-1]):
                return ", ".join(parts[:-1]), MuseotFISpider._clean_city(parts[-1]), None
            if MuseotFISpider.STREET_SUFFIX_RE.search(parts[-2]):
                return ", ".join(parts[:-1]), MuseotFISpider._clean_city(parts[-1]), None
            return text, None, None
        if " " in text and re.search(r"\d", text):
            head, _, tail = text.rpartition(" ")
            # Single-letter tails are stair/house letters (cf. "34 B").
            if head and len(tail) > 1 and not re.search(r"\d", tail):
                return head, tail, None
        return text, None, None

    def parse_phone(self, response: Response) -> str | None:
        # Structured per-museum phone <p> in the contact block; the footer
        # hotline lives outside this block and never matches. Text nodes are
        # joined per <p> so housenumber+postcode runs (e.g. "3 99600") never
        # read as a phone. A leading "(+358)" unwraps to "+358"; notes and
        # second numbers are dropped, first number wins.
        texts = [
            " ".join(p.xpath(".//text()").getall()).strip()
            for p in response.xpath("//div[@class='museon_tiedot']/p[not(a)]")
        ]
        texts = [t for t in (re.sub(r"\s+", " ", t) for t in texts) if t]
        for text in texts[1:]:
            text = re.sub(r"^\(\+358\)", "+358", text)
            if match := self.PHONE_RE.search(text):
                if len(re.sub(r"\D", "", match.group(0))) >= 6:
                    return match.group(0).strip()
        return None

    def parse_hours(self, response: Response) -> OpeningHours | None:
        # Seasonally or renovation-closed museums carry free text instead
        # of a table and emit no hours.
        rows = response.xpath("//table[@class='aukioloajat']/tr")
        if not rows:
            self._stat("atp/museot_fi/empty/hours")
            return None
        oh = OpeningHours()
        has_open = False
        for row in rows:
            day_raw = "".join(row.xpath("./td[1]//text()").getall()).strip()
            hours_raw = "".join(row.xpath("./td[2]//text()").getall()).strip()
            if (day := DAYS_FI.get(day_raw)) is None:
                self._stat(f"atp/museot_fi/hours/unmapped_day/{day_raw or 'empty'}")
                continue
            if hours_raw.casefold() == "suljettu":
                oh.set_closed(day)
            elif match := self.HOURS_RE.match(hours_raw):
                try:
                    oh.add_range(day, match.group(1), match.group(2), time_format="%H:%M")
                except ValueError:
                    self._stat("atp/museot_fi/hours/bad_range")
                else:
                    has_open = True
            else:
                self._stat(f"atp/museot_fi/hours/unmapped_hours/{hours_raw[:24] or 'empty'}")
        if not has_open:
            self._stat("atp/museot_fi/empty/hours_all_closed")
            return None
        return oh
