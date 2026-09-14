import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

# The site's own internal district numbering does not follow the ISO 3166-2:PT
# order, so map it explicitly to the ISO 3166-2:PT subdivision codes.
DISTRICTS = {
    1: "PT-01",  # Aveiro
    2: "PT-02",  # Beja
    3: "PT-03",  # Braga
    4: "PT-04",  # Bragança
    5: "PT-05",  # Castelo Branco
    6: "PT-06",  # Coimbra
    7: "PT-08",  # Faro
    8: "PT-09",  # Guarda
    9: "PT-10",  # Leiria
    10: "PT-11",  # Lisboa
    11: "PT-12",  # Portalegre
    12: "PT-13",  # Porto
    13: "PT-20",  # Região Autónoma dos Açores
    14: "PT-30",  # Região Autónoma da Madeira
    15: "PT-14",  # Santarém
    16: "PT-15",  # Setúbal
    17: "PT-16",  # Viana do Castelo
    18: "PT-17",  # Vila Real
    19: "PT-18",  # Viseu
    20: "PT-07",  # Évora
}

DAY_LABELS = {
    "Seg. a Sex": ["Mo", "Tu", "We", "Th", "Fr"],
    "Sábado": ["Sa"],
    "Domingo": ["Su"],
}


class SparPTSpider(Spider):
    name = "spar_pt"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    start_urls = ["https://www.spar.pt/loja/resumo"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The store list (with id, name and coordinates) is embedded directly
        # in the page as a JS string literal, escaped with \uXXXX sequences
        # for characters like quotes; other unicode characters appear
        # unescaped, so only unescape the explicit \uXXXX sequences.
        if not (m := re.search(r"var lojasData = JSON\.parse\('(.*?)'\);", response.text, re.S)):
            return
        raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda mm: chr(int(mm.group(1), 16)), m.group(1))
        for store in json.loads(raw):
            yield response.follow(
                f"/loja/detalhe/{store['id']}/",
                callback=self.parse_store,
                cb_kwargs={"store": store},
            )

    def parse_store(self, response: Response, store: dict) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = store["id"]
        # A handful of records have a stray trailing comma baked into the
        # source's latitude value (e.g. "41.14461868518819,").
        item["lat"] = store["latitude"].rstrip(",")
        item["lon"] = store["longitude"].rstrip(",")
        item["website"] = response.url
        item["street_address"] = store["rua"].rstrip(", ").strip()

        if m := re.match(r"(\d{4}-\d{3})\s*(.*)", store["codpostal"]):
            item["postcode"] = m.group(1)
            item["city"] = m.group(2).strip()
        else:
            item["addr_full"] = store["codpostal"]

        state = DISTRICTS.get(store.get("distrito_id"))
        if not state and item.get("postcode"):
            # A few records have no distrito_id at all; the postcode prefix still
            # distinguishes the two autonomous regions from each other.
            prefix = int(item["postcode"][:2])
            if 90 <= prefix <= 94:
                state = "PT-30"  # Região Autónoma da Madeira
            elif 95 <= prefix <= 99:
                state = "PT-20"  # Região Autónoma dos Açores
        if state:
            item["state"] = state

        name = re.sub(r"\s+", " ", store["nome"]).strip()
        item["branch"] = name.removeprefix("SPAR").strip()
        item["name"] = "Spar"

        if phone := response.xpath('//span[contains(., "Telefone")]/following-sibling::text()[1]').get():
            if phone := phone.strip():
                item["phone"] = phone

        if email := response.xpath('//span[contains(., "Email")]/following-sibling::text()[1]').get():
            if email := email.strip():
                item["email"] = email

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        oh = OpeningHours()

        if "Horário</div>" not in response.text:
            return oh
        block = response.text.split("Horário</div>")[1].split("Contactos</div>")[0]

        for label, hours_text in re.findall(
            r'<span class="loja-detalhe-subtitulo">([^:<]+): </span>\s*([^<]+)<br>', block
        ):
            days = DAY_LABELS.get(label.strip())
            if not days:
                # "Feriados" (public holidays) is not a weekday and isn't modelled here
                continue

            hours_text = hours_text.strip()
            if "encerr" in hours_text.lower():
                oh.set_closed(days)
                continue

            for period in hours_text.split("|"):
                if "-" not in period:
                    continue
                # A handful of records use "." instead of ":" as the hour/minute separator.
                open_time, close_time = (t.strip().replace(".", ":") for t in period.split("-", 1))
                oh.add_days_range(days, open_time, close_time)

        return oh
