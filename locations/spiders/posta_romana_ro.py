import re
import unicodedata
from collections import defaultdict
from typing import Any, AsyncIterator

from scrapy import Request, Selector, Spider
from scrapy.http import FormRequest, Response
from scrapy.signals import spider_idle

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

API = "https://www.posta-romana.ro/cnpr-app/modules/gaseste-oficiu-postal/ajax/"

# Unit types ("tip unitate") listed by the finder that serve the public at a counter.
# The other types (county/zonal head offices, delivery-only "Oficiu Postal de Distribuire", courier hubs and
# mini hubs, international exchange offices, the stamp printing branch) are not post offices for the public.
PUBLIC_TYPES = {"Oficiu Postal", "Ghiseu Postal", "Agentii Postale", "AGD", ""}

# Phrases in the hours text meaning the unit is closed, suspended or merged into another unit.
INACTIVE = re.compile(
    r"fara activitate|nu are activitate|activitate(?:a)? suspen|activitate(?:a)? (?:a fost )?preluat"
    r"|temporar activitate asigurata|suspenda temporar programul"
    # text that starts by naming the unit now serving these localities instead
    r"|^\W*(?:localitatile .* deservite de|deserveste|activitate(?:a)? (?:este )?asigurata de"
    r"|actititate asigurata de|activitate de prezentare se realizeaza la)"
)

DAYS_RO = {
    "l": "Mo",
    "luni": "Mo",
    "ma": "Tu",
    "marti": "Tu",
    "mi": "We",
    "miercuri": "We",
    "j": "Th",
    "joi": "Th",
    "v": "Fr",
    "vi": "Fr",
    "vineri": "Fr",
    "s": "Sa",
    "sambata": "Sa",
    "d": "Su",
    "duminica": "Su",
}
DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().replace("–", "-").replace("—", "-")


class PostaRomanaROSpider(Spider):
    name = "posta_romana_ro"
    item_attributes = {"operator": "Poșta Română", "operator_wikidata": "Q283175"}
    allowed_domains = ["www.posta-romana.ro"]
    start_urls = ["https://www.posta-romana.ro/gaseste-oficiu-postal.html"]

    async def start(self) -> AsyncIterator[Request]:
        # Items are held back until every office has been fetched so that coordinates shared by several
        # offices (the site falls back to geocoding a place name) can be recognised and dropped.
        self.items = []
        self.crawler.signals.connect(self.flush_items, signal=spider_idle)
        for url in self.start_urls:
            yield Request(url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The finder works county -> locality -> list of offices -> office details, each an AJAX POST
        # returning an HTML fragment wrapped in JSON.
        for county in response.xpath('//select[@id="judet_1"]/option/@value').getall():
            if not county:
                continue
            yield FormRequest(
                API + "cauta_orase.php?q=",
                formdata={"k_judet": county, "k_lang": "ro", "postcollect": ""},
                callback=self.parse_localities,
                cb_kwargs={"county": county},
            )

    def parse_localities(self, response: Response, county: str) -> Any:
        for locality in Selector(text=response.json()["formular"]).xpath("//option/@value").getall():
            if not locality:
                continue
            yield FormRequest(
                API + "cautare_oficiu.php?q=",
                formdata={"k_judet": county, "k_localitate": locality, "k_lang": "ro"},
                callback=self.parse_offices,
                cb_kwargs={"county": county, "locality": locality.strip()},
            )

    def parse_offices(self, response: Response, county: str, locality: str) -> Any:
        for line in Selector(text=response.json().get("formular") or "").xpath(
            '//div[contains(@class, "oficiu-postal-line")]'
        ):
            cells = [" ".join(" ".join(c.xpath(".//text()").getall()).split()) for c in line.xpath("./div")]
            unit_id = re.search(r"detalii_oficiu_by_id\('(\d+)'\)", line.get())
            if not unit_id or len(cells) < 3:
                continue
            if cells[1] not in PUBLIC_TYPES or cells[0].startswith("Compania Na"):
                self.crawler.stats.inc_value(f"atp/posta_romana_ro/skipped_type/{cells[1]}")
                continue
            yield FormRequest(
                API + "detalii_oficiu.php?q=",
                formdata={"k_id_unitate": unit_id.group(1), "k_lang": "ro"},
                callback=self.parse_office,
                cb_kwargs={
                    "unit_id": unit_id.group(1),
                    "name": cells[0],
                    "unit_type": cells[1],
                    "county": county,
                    "locality": locality,
                },
            )

    def parse_office(
        self, response: Response, unit_id: str, name: str, unit_type: str, county: str, locality: str
    ) -> Any:
        data = response.json()
        sel = Selector(text=data.get("formular") or "")
        fields = {}
        for p in sel.xpath("//p[b]"):
            label = " ".join(p.xpath("./b//text()").getall()).strip().rstrip(":")
            fields[label] = " ".join(" ".join(p.xpath("./text()").getall()).split())
        hours = fields.get("Orar", "")
        if INACTIVE.search(normalise(hours)):
            self.crawler.stats.inc_value("atp/posta_romana_ro/inactive")
            return

        item = Feature()
        item["ref"] = unit_id
        item["branch"] = name
        item["state"] = county.strip()
        item["city"] = locality
        try:
            lat, lon = float(data.get("lat") or 0), float(data.get("lon") or 0)
        except ValueError:
            lat = lon = 0
        if 20 < lat < 30 and 43 < lon < 49:
            lat, lon = lon, lat
        if 43.5 < lat < 48.4 and 20.2 < lon < 29.8:  # Romania
            item["lat"], item["lon"] = lat, lon
        elif lat or lon:
            self.crawler.stats.inc_value("atp/posta_romana_ro/coordinates_outside_romania")

        # e.g. "Cluj, Sat Apahida, Str. Libertăţii, nr. 96, Comuna Apahida cod poştal oficiu:407035"
        address = fields.get("Adresa", "")
        if m := re.search(r"cod po[sşș]tal oficiu:\s*(\d{6})", address):
            item["postcode"] = m.group(1)
            address = address[: m.start()]
        item["addr_full"] = address.strip(" ,")

        contacts = [" ".join(t.split()) for t in sel.xpath("//ul/li/text()").getall() if t.strip()]
        item["email"] = next((c for c in contacts if "@" in c), None)
        item["phone"] = "; ".join(c for c in contacts if "@" not in c and re.search(r"\d{3}", c)) or None

        item["opening_hours"] = self.parse_hours(hours)
        if unit_type:
            item["extras"]["post_office:type"] = unit_type
        apply_category(Categories.POST_OFFICE, item)
        self.items.append(item)

    def flush_items(self) -> None:
        self.crawler.signals.disconnect(self.flush_items, signal=spider_idle)
        self.crawler.engine.crawl(Request(self.start_urls[0], callback=self.yield_items, dont_filter=True))

    def yield_items(self, response: Response) -> Any:
        # When the site has no position for an office it geocodes a place name, so unrelated offices end up
        # on the same point (e.g. over a hundred village agencies in Timiș on central Timișoara). Drop any
        # point shared by offices with different addresses; counters in one building keep theirs.
        addresses = defaultdict(set)
        for item in self.items:
            if item.get("lat"):
                addresses[(item["lat"], item["lon"])].add(item["addr_full"])
        for item in self.items:
            if item.get("lat") and len(addresses[(item["lat"], item["lon"])]) > 1:
                item["lat"] = item["lon"] = None
                self.crawler.stats.inc_value("atp/posta_romana_ro/shared_coordinates_dropped")
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        # e.g. "L-V: 09:00 – 15:00", "L, Mi, V: 08:00-16:00; Ma, J: 11:00-19:00",
        # "Luni, Miercuri si Vineri: 14:00 - 14:30 Marti si Joi: 11:00 -11:30"
        text = normalise(text)
        if re.search(r"pensi|achitare|perioada de baza|audient", text):
            return None  # alternating schedules for pension-payment days; audience hours
        # Drop notes on temporary schedules and customs hours that follow the regular hours.
        text = re.split(
            r"\(|\bvama\b|program(?:ul)? (?:de )?vam|activitatea de prezentare|\s-\s*(?:in|din|incepand)\b|\bin perioada|\bdin data|\bincepand",
            text,
        )[0]
        oh = OpeningHours()
        found = False
        for days_text, times_text in re.findall(
            r"([a-z][a-z ,.\-]*?)\s*[:=]?\s*((?:\d{1,2}[:.]\d{2}\s*-\s*\d{1,2}[:.]\d{2}(?:\s*(?:,|si|/|;)\s*(?=\d))?)+)",
            text,
        ):
            days = []
            for token in re.findall(r"[a-z]+(?:\s*-\s*[a-z]+)?", days_text):
                if token in ("si", "program", "orar"):
                    continue
                if "-" in token:
                    a, b = (DAYS_RO.get(t.strip()) for t in token.split("-", 1))
                    if not a or not b:
                        return None
                    days += DAY_ORDER[DAY_ORDER.index(a) : DAY_ORDER.index(b) + 1]
                elif token in DAYS_RO:
                    days.append(DAYS_RO[token])
                else:
                    return None
            for start, end in re.findall(r"(\d{1,2}[:.]\d{2})\s*-\s*(\d{1,2}[:.]\d{2})", times_text):
                for day in days:
                    oh.add_range(day, start.replace(".", ":"), end.replace(".", ":"))
                    found = True
        return oh if found else None
