import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "mo": "Mo",
    "di": "Tu",
    "mi": "We",
    "do": "Th",
    "fr": "Fr",
    "sa": "Sa",
    "so": "Su",
}

# The embedded JSON blob uses explicit JS escapes (\uXXXX, \xXX, \n, \", \/, \\)
# but emits non-ASCII characters as raw UTF-8 bytes. The ``unicode-escape`` codec
# mis-decodes those bytes as Latin-1, so unescape only the real JS escapes.
_JS_ESCAPE_RE = re.compile(r"\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)", re.DOTALL)
_JS_SIMPLE_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "0": "\0",
    '"': '"',
    "'": "'",
    "/": "/",
    "\\": "\\",
}


def _js_unescape(s: str) -> str:
    def replace(match: re.Match) -> str:
        esc = match.group(1)
        if esc[0] in ("u", "x"):
            return chr(int(esc[1:], 16))
        return _JS_SIMPLE_ESCAPES.get(esc, esc)

    return _JS_ESCAPE_RE.sub(replace, s)


class CommerzbankDESpider(CrawlSpider):
    name = "commerzbank_de"
    item_attributes = {"brand": "Commerzbank", "brand_wikidata": "Q157617"}
    allowed_domains = ["commerzbank.de"]
    start_urls = ["https://filialsuche.commerzbank.de/de/branch-name"]

    rules = [Rule(LinkExtractor(allow=r"/de/branch-name/.+"), callback="parse_details")]

    def parse_hours(self, store_info) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            try:
                if open_t := store_info.get(f"{day}MorgenVon"):
                    opening_hours.add_range(
                        day=DAY_MAPPING[day],
                        open_time=open_t,
                        close_time=store_info[f"{day}MorgenBis"],
                        time_format="%H:%M",
                    )
            except (KeyError, ValueError):
                pass
        return opening_hours

    def parse_details(self, response):
        if match := re.search(
            r"const decodedResults = JSON\.parse\(\$\(\"<div\/>\"\)\.html\(\"(.+?)\"\)\.text\(\)\);", response.text
        ):
            raw_data = match.group(1)
            clean_json = _js_unescape(raw_data)
            try:
                data = json.loads(clean_json)
            except json.JSONDecodeError:
                return

            for branch in data:
                properties = {
                    "name": branch.get("name") or branch.get("orgTypName"),
                    "ref": branch["id"],
                    "street_address": branch.get("anschriftStrasse"),
                    "city": branch.get("anschriftOrt"),
                    "postcode": branch.get("anschriftPostleitzahl"),
                    "country": "DE",
                    "lat": float(branch["position"][0]),
                    "lon": float(branch["position"][1]),
                    "phone": branch.get("telefon", ""),
                    "website": response.url,
                    "extras": {
                        "fax": branch.get("telefax", ""),
                        "barriere_type": branch.get("barriereTyp", ""),
                        "cash_register": branch.get("kasse", ""),
                        "vault": branch.get("vault", ""),
                        "cashback": branch.get("cashback", ""),
                        "cashgroup": branch.get("cashgroup", ""),
                    },
                }

                properties["opening_hours"] = self.parse_hours(branch)

                apply_category(Categories.BANK, properties)
                apply_yes_no(Extras.ATM, properties, bool(branch.get("geldautomat")))

                yield Feature(**properties)
