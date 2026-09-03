import re
from typing import Iterable

from scrapy import Request
from scrapy.http import TextResponse
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_FR = {
    "lundi": "Mo",
    "mardi": "Tu",
    "mercredi": "We",
    "jeudi": "Th",
    "vendredi": "Fr",
    "samedi": "Sa",
    "dimanche": "Su",
}

LAT_RE = re.compile(r'defaultLat\s*=\s*parseFloat\("(-?\d+\.\d+)"\)')
LON_RE = re.compile(r'defaultLong\s*=\s*parseFloat\("(-?\d+\.\d+)"\)')


class BleuforetFRSpider(Spider):
    name = "bleuforet_fr"
    item_attributes = {"brand": "Bleuforêt", "brand_wikidata": "Q2906440"}
    allowed_domains = ["bleuforet.fr"]
    start_urls = ["https://www.bleuforet.fr/fr/magasins"]

    def parse(self, response: TextResponse) -> Iterable[Request]:
        for href in response.css('a[href*="/fr/magasins/"]::attr(href)').getall():
            if re.search(r"/fr/magasins/\d+-", href):
                yield response.follow(href, callback=self.parse_store)

    def parse_store(self, response: TextResponse) -> Iterable[Feature]:
        name = (response.css("h1::text").get() or "").strip()
        if not name:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1].split("-", 1)[0]
        item["name"] = name
        item["website"] = response.url
        item["country"] = "FR"

        if "bleuforêt" not in name.lower() and "bleuforet" not in name.lower():
            item["brand"] = None
            item["brand_wikidata"] = None

        addr = self.get_detail(response, "Adresse")
        if addr:
            m = re.match(r"(?P<street>.+?)(?P<postcode>\d{5})\s*(?P<city>.+)", addr)
            if m:
                item["street_address"] = m.group("street").strip()
                item["postcode"] = m.group("postcode")
                item["city"] = m.group("city").strip()
            else:
                item["addr_full"] = addr

        item["phone"] = self.get_detail(response, "Téléphone")

        email_encoded = response.xpath(
            '//tr[normalize-space(td[1])="Email"]//@data-cfemail'
        ).get()
        if email_encoded:
            item["email"] = self.decode_cf_email(email_encoded)

        item["opening_hours"] = self.parse_hours(response)

        lat, lon = self.extract_latlon(response)
        if lat and lon:
            item["lat"] = lat
            item["lon"] = lon
        else:
            self.crawler.stats.inc_value("atp/bleuforet_fr/no_geometry")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item

    @staticmethod
    def get_detail(response: TextResponse, label: str) -> str:
        return response.xpath(
            f'normalize-space(//table//tr[normalize-space(td[1])="{label}"]/td[2])'
        ).get("")

    @staticmethod
    def decode_cf_email(encoded: str) -> str:
        r = int(encoded[:2], 16)
        return "".join(chr(int(encoded[i:i + 2], 16) ^ r) for i in range(2, len(encoded), 2))

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()

        for row in response.xpath("//table//tr"):
            cells = [c.strip() for c in row.xpath(".//text()").getall() if c.strip()]
            if len(cells) < 2:
                continue

            day_fr = cells[0].rstrip(":").lower()
            if day_fr not in DAY_FR:
                continue

            hours_str = " ".join(cells[1:])
            if "fermé" in hours_str.lower():
                continue

            times = [f"{int(h):02d}:{m or '00':0>2}" for h, m in re.findall(r"(\d{1,2})h(\d{0,2})", hours_str)]

            for i in range(0, len(times), 2):
                if i + 1 < len(times):
                    oh.add_range(DAY_FR[day_fr], times[i], times[i + 1], time_format="%H:%M")

        return oh

    @staticmethod
    def extract_latlon(response: TextResponse):
        lat = LAT_RE.search(response.text)
        lon = LON_RE.search(response.text)
        if lat and lon:
            return lat.group(1), lon.group(1)
        return None, None
