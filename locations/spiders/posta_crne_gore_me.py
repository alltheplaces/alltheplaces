import json
import re
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_TOKENS = {"pon": "Mo", "uto": "Tu", "sri": "We", "cet": "Th", "pet": "Fr", "sub": "Sa", "ned": "Su"}
# "08:00h - 15:00h", "08h-16h", "07,00-14,00", "07.00-10.00"
TIME_RANGE = r"(\d{1,2})(?:[.:,](\d{2}))?\s*h?\s*[-–]\s*(\d{1,2})(?:[.:,](\d{2}))?\s*h?"


def jquery_param(value: Any, prefix: str) -> list[tuple[str, str]]:
    """Flatten nested data the way jQuery.param() form-encodes it ("a[b][]=c")."""
    if isinstance(value, dict):
        return [pair for k, v in value.items() for pair in jquery_param(v, f"{prefix}[{k}]")]
    if isinstance(value, list):
        return [pair for v in value for pair in jquery_param(v, f"{prefix}[]")]
    if isinstance(value, bool):
        return [(prefix, "true" if value else "false")]
    return [(prefix, "" if value is None else str(value))]


class PostaCrneGoreMESpider(Spider):
    name = "posta_crne_gore_me"
    item_attributes = {"operator": "Pošta Crne Gore", "operator_wikidata": "Q1320833"}
    allowed_domains = ["www.postacg.me"]
    start_urls = ["https://www.postacg.me/centar-za-korisnike/lokacije-poslovnica/"]
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_DELAY": 1}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The map element carries every office's coordinates keyed by WordPress post id; the listing grid
        # below it (JetEngine) shows 12 office cards per page and loads the rest through admin AJAX.
        coords = {}
        for markers in response.xpath("//@data-markers").getall():
            for marker in json.loads(markers):
                coords[str(marker["id"])] = marker["latLang"]

        yield from self.parse_cards(response, coords)

        grid = response.xpath('//div[contains(@class, "jet-listing-grid__items")][@data-nav]')
        nav = json.loads(grid.xpath("@data-nav").get())
        page_settings = {
            "post_id": grid.xpath("@data-queried-id").get("").split("|")[0],
            "queried_id": grid.xpath("@data-queried-id").get(""),
            "element_id": grid.xpath("ancestor::div[@data-widget_type][1]/@data-id").get(""),
        }
        for page in range(2, int(grid.xpath("@data-pages").get("1")) + 1):
            formdata = [("action", "jet_engine_ajax"), ("handler", "listing_load_more")]
            formdata += jquery_param(nav["query"], "query")
            formdata += jquery_param(nav["widget_settings"], "widget_settings")
            formdata += jquery_param(page_settings | {"page": page}, "page_settings")
            yield FormRequest(
                url=response.url, formdata=formdata, callback=self.parse_ajax, cb_kwargs={"coords": coords}
            )

    def parse_ajax(self, response: Response, coords: dict, **kwargs: Any) -> Any:
        yield from self.parse_cards(Selector(text=response.json()["data"]["html"]), coords)

    def parse_cards(self, selector: Selector, coords: dict) -> Any:
        for card in selector.xpath('//div[contains(@class, "jet-listing-grid__item")][@data-post-id]'):
            # Card text is a run of "Label:" / value pairs: Mjesto, Regionalni Centar, Adresa,
            # Poštanski broj, Radno vrijeme, Telefon.
            texts = [t.strip() for t in card.xpath(".//text()").getall() if t.strip()]
            fields, label = {}, None
            for text in texts:
                if text.endswith(":"):
                    label = text[:-1]
                    fields[label] = ""
                elif label:
                    fields[label] = (fields[label] + " " + text).strip()

            ref = card.xpath("@data-post-id").get()
            item = Feature()
            item["ref"] = ref
            if point := coords.get(ref):
                item["lat"], item["lon"] = point["lat"], point["lng"]
            name = re.sub(r"\s+", " ", fields.get("Mjesto", "")).strip()  # "PODGORICA 1", "85321 Luštica"
            item["branch"] = re.sub(r"^\d{5}\s*", "", name) or None
            item["street_address"] = fields.get("Adresa") or None
            item["postcode"] = (re.search(r"\b\d{5}\b", fields.get("Poštanski broj", "")) or [None])[0]
            item["phone"] = fields.get("Telefon") or None
            item["opening_hours"] = self.parse_hours(fields.get("Radno vrijeme", ""))
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        # Most cards give only a time window with no days ("08:00h - 15:00h"); those are left unset rather
        # than guessed. Days, when present, follow the window: "08h-16h, pon-pet", "07:00h - 14:00h (Pon-Sub)",
        # "07:00h -12:00h,pon, srijeda, petak". Some windows include the delivery round, with the counter
        # part spelled out: "07:00h - 14:00h, Pon-Sub (od 07.00-10.00 rad u pošti, od 10.00-14.00 rad na rejonu)".
        if "sezon" in text.lower():
            return None  # separate in-season hours ("a u sezoni od ...") without dates
        if counter := re.search(TIME_RANGE + r"\s*(?:rad\s+)?u\s+pošti", text, re.IGNORECASE):
            window = counter
        elif not (window := re.search(TIME_RANGE, text)):
            return None
        day_text = re.sub(TIME_RANGE, " ", text).lower()
        tokens = re.findall(r"\b(pon|uto|sri|[čc]et|pet|sub|ned)[a-zčćšž]*\b(\s*-\s*)?", day_text)
        days = []
        for i, (token, dash) in enumerate(tokens):
            day = DAY_TOKENS[token.replace("č", "c")]
            if dash and i + 1 < len(tokens):
                end = DAY_TOKENS[tokens[i + 1][0].replace("č", "c")]
                days += DAYS[DAYS.index(day) : DAYS.index(end) + 1]
            elif day not in days:
                days.append(day)
        if not days:
            return None
        h1, m1, h2, m2 = window.groups()
        oh = OpeningHours()
        oh.add_days_range(days, f"{h1}:{m1 or '00'}", f"{h2}:{m2 or '00'}")
        return oh
