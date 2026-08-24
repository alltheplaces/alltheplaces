import re
from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES

# Unicode "Braille Pattern Blank" (U+2800) is used by the source site as a
# placeholder for an unset e-mail address.
BLANK_PLACEHOLDER = "⠀"


class HyundaiUYSpider(JSONBlobSpider):
    name = "hyundai_uy"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com.uy"]
    start_urls = ["https://www.hyundai.com.uy/red-hyundai"]

    def extract_json(self, response: Response) -> list:
        js_blob = response.xpath("//script[contains(text(), 'mapa_concesionarios')]/text()").get()
        locations = loads(re.search(r"mapa_concesionarios\s*=\s*(\[.*?\]);", js_blob, re.S).group(1))

        # Dealers are listed once per service they offer ("tipo_id": 1 =
        # Venta/sales, 2 = Talleres/workshop, 3 = Repuestos/parts, plus some
        # unlabelled ids 4-8 of unclear meaning). Group by "concesionario_id"
        # (a stable per-branch id) so each physical branch is only yielded
        # once, retaining the set of service types it offers.
        dealers = {}
        for location in locations:
            dealer = dealers.setdefault(location["concesionario_id"], {**location, "tipo_ids": set()})
            dealer["tipo_ids"].add(location["tipo_id"])

        return list(dealers.values())

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = str(feature["concesionario_id"])
        feature["name"] = feature["titulo"].strip()

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["name"] = self.item_attributes["brand"]

        if item.get("email") in (None, "", BLANK_PLACEHOLDER, "<br>"):
            item["email"] = None

        if phone := item.get("phone"):
            phone = re.sub(r"\bcel\.?:?\s*", "", phone, flags=re.IGNORECASE)
            phone = phone.replace("<br>", ", ").strip(" ,")
            if len(re.sub(r"\D", "", phone)) < 6:
                # A small number of records have an address (not a phone
                # number) erroneously present in this field.
                phone = None
            item["phone"] = phone

        if hours := feature.get("horarios"):
            hours = hours.replace("<br>", " ").replace("Horario:", "")
            hours = re.sub(r"\bhrs?\.?\b", "", hours, flags=re.IGNORECASE)
            hours = re.sub(r"\s+", " ", hours).strip(" .,")
            if hours:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours, days=DAYS_ES, delimiters=DELIMITERS_ES)

        tipo_ids = feature["tipo_ids"]
        if tipo_ids & {1, 4, 5, 6, 7, 8}:
            # "Venta" (sales), plus the unlabelled ids which co-occur with
            # sales branches far more often than with workshop-only ones.
            apply_category(Categories.SHOP_CAR, item)
        elif 2 in tipo_ids:
            apply_category(Categories.SHOP_CAR_REPAIR, item)  # "Talleres"
        elif 3 in tipo_ids:
            apply_category(Categories.SHOP_CAR_PARTS, item)  # "Repuestos"
        else:
            apply_category(Categories.SHOP_CAR, item)

        yield item
