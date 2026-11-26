import json
import re
from html import unescape

import reverse_geocoder
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS, DAYS_FR, DELIMITERS_EN, NAMED_DAY_RANGES_EN, OpeningHours
from locations.items import Feature


class YogurtFactorySpider(Spider):
    name = "yogurt_factory"
    item_attributes = {"brand": "Yogurt Factory", "brand_wikidata": "Q104600544", "name": "Yogurt Factory"}
    start_urls = ["https://yogurtfactory.fr/nos-shops/"]

    # Title keywords for shops without coordinates, where the .fr website fallback would give the wrong country.
    TITLE_COUNTRY_HINTS = {
        "TASHKENT": "UZ",
        "KUALA LUMPUR": "MY",
        "SALY": "SN",
        "LIBREVILLE": "GA",
        "LUXEMBOURG": "LU",
        "CHARLEROI": "BE",
        "LIÈGE": "BE",
        "LIEGE": "BE",
        "GUYANE": "GF",
        "CALÉDONIE": "NC",
        "CALEDONIE": "NC",
    }
    # Moves a leading "10:00-20:00 du lundi au samedi" time range after its days.
    DAY = r"(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|tous les jours)"
    SWAP_TIMES_FIRST = re.compile(
        rf"(\d{{1,2}}:\d{{2}}(?:\s*[-–à,]\s*\d{{1,2}}:\d{{2}})*)\s+(?:(?:du|de|le|et)\s+)?({DAY}(?:\s*(?:au|à|et|[-–])\s*{DAY})*)(?!\s*\d)",
        re.IGNORECASE,
    )

    def parse(self, response: Response):
        shops = json.loads(re.search(r"var yogurt = (\{.*?\});", response.text, re.S).group(1))["shops"]
        for shop in shops:
            card = Selector(text=shop["html"])
            item = Feature()
            item["ref"] = str(shop["id"])
            item["branch"] = unescape(shop["title"])
            item["website"] = shop["lien"]
            apply_category(Categories.ICE_CREAM, item)

            if shop["lat"] and shop["lng"]:
                item["lat"] = float(shop["lat"])
                item["lon"] = float(shop["lng"])
                if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                    item["country"] = result["cc"]
            else:
                title = shop["title"].upper()
                if hint := next((cc for kw, cc in self.TITLE_COUNTRY_HINTS.items() if kw in title), None):
                    item["country"] = hint

            if address := card.xpath("//p[not(@class)]/text()").get():
                address = re.sub(r"\s+", " ", address).strip()
                if match := re.match(r"^(.*?)[\s,]+(\d{4,5})\s+(.+)$", address) or re.match(
                    r"^(.*?)[\s,]+(\d{4,5})$", address
                ):
                    item["street_address"] = match.group(1)
                    item["postcode"] = match.group(2)
                    if match.lastindex == 3:
                        item["city"] = match.group(3)
                else:
                    item["addr_full"] = address

            if image := card.xpath("//img/@src").re_first(r"https?://\S+"):
                item["image"] = image

            if schedule := card.xpath("//p[@class='schedule']/text()").get():
                text = re.sub(r"(\d{1,2})h(\d{2})?", lambda m: f"{m.group(1)}:{m.group(2) or '00'}", schedule)
                text = re.sub(r"minuit", "24:00", text, flags=re.IGNORECASE)
                segments = []
                for segment in text.splitlines():
                    segment = segment.strip()
                    if segment[:1].isdigit():
                        previous = None
                        while previous != segment:
                            previous = segment
                            segment = self.SWAP_TIMES_FIRST.sub(r"\2 \1", segment)
                    segments.append(segment)
                oh = OpeningHours()
                oh.add_ranges_from_string(
                    " ".join(segments),
                    days=DAYS_FR,
                    named_day_ranges={**NAMED_DAY_RANGES_EN, "Tous Les Jours": DAYS},
                    delimiters=DELIMITERS_EN + [":", "à", "au", "de", "le", "et", ",", "|"],
                    closed=CLOSED_FR,
                )
                item["opening_hours"] = oh

            yield item
