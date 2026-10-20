import json
import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Serbian (Latin) weekday tokens used in the detail fragment's opening hours -> ATP day codes.
DAY_TOKENS = {
    "pon": "Mo",  # ponedeljak
    "uto": "Tu",  # utorak
    "sre": "We",  # sreda
    "cet": "Th",  # četvrtak (č normalised to c)
    "pet": "Fr",  # petak
    "sub": "Sa",  # subota
    "ned": "Su",  # nedelja
}
# A weekday label immediately preceding a "HH.MM-HH.MM" range (per-day schedules).
DAY_RANGE_RE = re.compile(
    r"(pon|uto|sre|[čc]et|pet|sub(?:ota)?|ned(?:elja)?)\s*\.?\s*:?\s*(\d{1,2})\.(\d{2})\s*-\s*(\d{1,2})\.(\d{2})",
    re.IGNORECASE,
)
RANGE_RE = re.compile(r"(\d{1,2})\.(\d{2})\s*-\s*(\d{1,2})\.(\d{2})")


class PostaSrbijeRSSpider(Spider):
    name = "posta_srbije_rs"
    item_attributes = {"operator": "Пошта Србије", "operator_wikidata": "Q769311"}
    allowed_domains = ["www.posta.rs"]
    start_urls = ["https://www.posta.rs/lat/alati/lokacije.aspx"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The locator embeds a JSON array of markers carrying only coordinates and a type; the
        # address/hours come from a per-location detail endpoint, one request per POI.
        for location in json.loads(response.xpath('//p[@class="pom"]/text()').get()):
            if location["objekattip"] not in ("POSTA", "PAKETOMAT", "ATM"):
                continue  # skip detached counters ("izdvojeni šalter")
            yield JsonRequest(
                url="https://www.posta.rs/alati/pronadji/lokacije-user-control-data.aspx"
                "?id={}&tip={}&lokstranice=lat".format(location["id"], location["tip"]),
                callback=self.parse_location,
                cb_kwargs={
                    "ref": str(location["id"]),
                    "lat": location["lat"],
                    "lon": location["lng"],
                    "poi_type": location["objekattip"],
                },
            )

    def parse_location(self, response: Response, ref: str, lat: float, lon: float, poi_type: str, **kwargs: Any) -> Any:
        # The endpoint returns (as a JSON string) an HTML fragment of "<b>Label:</b> value<br/>"
        # pairs with Serbian labels; DictParser keys off English field names and maps none of them,
        # so the fields are read out by their label via XPath.
        fragment = Selector(text=json.loads(response.text))
        fields = {}
        for label in fragment.xpath("//b"):
            fields[label.xpath("normalize-space()").get().rstrip(":")] = label.xpath(
                "normalize-space(following-sibling::text()[1])"
            ).get()

        name = fields.get("Naziv", "")
        item = Feature()
        item["ref"] = ref
        item["lat"] = lat
        item["lon"] = lon
        item["street_address"] = fields.get("Adresa")
        item["city"] = re.sub(r"\s*\(.*\)$", "", fields.get("Lokacija", "")) or None  # drop "(municipality)"
        if postcode := re.match(r"\d{5}", name):
            item["postcode"] = postcode.group()

        if poi_type == "ATM":
            apply_category(Categories.ATM, item)  # standalone "BANKOMAT" records; no hours/phone/branch
        elif poi_type == "PAKETOMAT":
            item["opening_hours"] = self.parse_hours(fragment)
            apply_category(Categories.PARCEL_LOCKER, item)  # "Naziv" is just the generic type word, so no branch
        else:  # POSTA
            item["branch"] = re.sub(r"^\d{5}\s*", "", name) or None  # "11000 BEOGRAD 6" -> "BEOGRAD 6"
            item["phone"] = fields.get("Telefon")
            item["opening_hours"] = self.parse_hours(fragment)
            apply_category(Categories.POST_OFFICE, item)
        yield item

    def parse_hours(self, fragment: Selector) -> OpeningHours:
        # Two layouts occur: a bare "HH.MM-HH.MM" (the Mon-Fri window) optionally followed by
        # "subota:"/"nedelja:" nodes, or a single per-day line "pon. 07.00-14.00 uto. ...". In the
        # per-day layout closed days are simply omitted, so a range is only fanned across Mon-Fri
        # when it carries no weekday label.
        opening_hours = OpeningHours()
        hours_text = '//text()[preceding-sibling::b[1][starts-with(normalize-space(), "Radno vreme")]]'
        for line in fragment.xpath(hours_text).getall():
            try:
                if labelled := DAY_RANGE_RE.findall(line):
                    for token, h1, m1, h2, m2 in labelled:
                        day = DAY_TOKENS[token[:3].lower().replace("č", "c")]
                        opening_hours.add_range(day, "{}:{}".format(h1, m1), "{}:{}".format(h2, m2))
                elif hours := RANGE_RE.search(line):
                    for day in DAYS[:5]:
                        opening_hours.add_range(
                            day, "{}:{}".format(hours[1], hours[2]), "{}:{}".format(hours[3], hours[4])
                        )
            except (KeyError, ValueError):
                self.crawler.stats.inc_value("atp/{}/hours/failed".format(self.name))
        return opening_hours
