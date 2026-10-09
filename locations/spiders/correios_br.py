import re
from html import unescape
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BR, OpeningHours, day_range, sanitise_day
from locations.items import Feature

STATES = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]  # fmt: skip

# Unit names start with the unit type. Only "AC" (Agência de Correios) units are run by Correios itself.
PARTNER_TYPES = {
    "AGF": "Agência de Correios Franqueada",  # franchised agency run by a private business
    "ACF": "Agência de Correios Franqueada",  # franchised agency (older contract model)
    "AGC": "Agência de Correios Comunitária",  # community agency run by a municipality or other partner
    "ACC": "Agência de Correios Comercial",  # older-style commercial (contracted) agency
    "LCF": "Loja de Correios Franqueada",  # franchised shop
    "PONTO DE COLETA": "Ponto de Coleta",  # parcel drop-off point in a third-party business
    "CEL": "CEL",  # small counters in remote towns and resorts, listed apart from the "AC" agencies
}


class CorreiosBRSpider(Spider):
    name = "correios_br"
    item_attributes = {"operator": "Empresa Brasileira de Correios e Telégrafos", "operator_wikidata": "Q3375004"}
    allowed_domains = ["buscaagencia.correios.com.br"]
    base = "https://buscaagencia.correios.com.br/app/carrega/"
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    async def start(self) -> AsyncIterator[Request]:
        for state in STATES:
            yield Request(
                f"{self.base}carrega_municipio.php?cmbEstado={state}",
                callback=self.parse_municipalities,
                cb_kwargs={"state": state},
            )

    def parse_municipalities(self, response: Response, state: str) -> Any:
        for municipality in response.json()["arrayMunicipios"]:
            # The agency search takes the numeric municipality code (ABAN83), not its name. An empty
            # neighbourhood returns every unit in the municipality.
            yield Request(
                f"{self.base}carrega_agencia_localidade.php?hddClientHours=12&cmbEstado={state}"
                f"&cmbMunicipio={municipality['ABAN83']}&cmbBairro=",
                callback=self.parse_units,
                cb_kwargs={"state": state, "city": municipality["MUNICIPIO"]},
            )

    def parse_units(self, response: Response, state: str, city: str) -> Any:
        # An HTML table: each unit is a "base-<CODIGO_MCU>" row followed by a "detalhe-<CODIGO_MCU>" row.
        for code, base, detail in re.findall(
            r'<tr id="base-(\w+)">(.*?)<tr id="detalhe-\1"[^>]*>(.*?)(?=<tr id="base-|</tbody>)', response.text, re.S
        ):
            name = self.text(re.search(r'class="nome-agencia"[^>]*>(.*?)</span>', base, re.S))
            if not name:
                continue
            item = Feature()
            item["ref"] = code
            # The address may continue on a second line (e.g. a complement or reference point).
            item["street_address"] = ", ".join(
                filter(None, map(self.text, re.findall(r'class="endereco-agencia"[^>]*>(.*?)</span>', base, re.S)))
            )
            item["city"] = city
            item["state"] = state
            # Units without a known location have latitude="0" longitude="0".
            if (lat := re.search(r'latitude="([-\d.]+)"\s+longitude="([-\d.]+)"', base)) and float(lat.group(1)):
                item["lat"], item["lon"] = lat.group(1), lat.group(2)
            fields = [
                self.text(f) for f in re.findall(r'<span\s+class="td-detalhe-agencia">(.*?)</span>', detail, re.S)
            ]
            for field in fields:
                if field.startswith("CEP:"):
                    item["postcode"] = field.removeprefix("CEP:").strip()
            item["opening_hours"] = self.parse_hours(
                re.findall(r'<span class="td-detalhe-agencia">\s*([^<:]+):<br>([^<]*)<', detail)
            )
            if status := self.text(re.search(r'class="situacao-agencia"[^>]*>(.*?)</span>', base, re.S)):
                item["extras"]["note"] = status

            unit_type = next((t for t in ["AC", *PARTNER_TYPES] if name.startswith(t + " ")), None)
            if unit_type == "AC":
                item["branch"] = name.removeprefix("AC ")
                apply_category(Categories.POST_OFFICE, item)
            elif name.startswith("LOCKER "):
                item["name"] = name
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                # Franchised (AGF, ACF, LCF), community (AGC), contracted (ACC) agencies and drop-off points are
                # run by other businesses or municipalities on behalf of Correios.
                if not unit_type:
                    self.logger.warning("Unexpected unit type: %s (%s)", name, code)
                item["name"] = name
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:type"] = PARTNER_TYPES.get(unit_type, name.split()[0])
                apply_category(Categories.GENERIC_POI, item)
            yield item

    @staticmethod
    def text(match) -> str:
        if match is None:
            return ""
        value = match.group(1) if isinstance(match, re.Match) else match
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()

    @staticmethod
    def parse_hours(rows: list[tuple[str, str]]) -> OpeningHours:
        # e.g. ("Segunda a sexta", "08:00 às 12:00 e 13:00 às 17:00"), ("Segunda, terÇa, quinta", "08:00 às 12:00");
        # weekend duty ("Plantão") hours and the last posting time ("Horário Limite de Postagem") are skipped.
        oh = OpeningHours()
        for label, value in rows:
            label = " ".join(label.split())
            if " a " in label:
                first, last = (sanitise_day(day, DAYS_BR) for day in label.split(" a ", 1))
                days = day_range(first, last) if first and last else []
            else:
                days = [sanitise_day(day, DAYS_BR) for day in label.split(",")]
            if not days or not all(days):
                continue
            for start, end in re.findall(r"(\d{1,2}:\d{2})\s*às\s*(\d{1,2}:\d{2})", value):
                oh.add_days_range(days, start, end)
        return oh
