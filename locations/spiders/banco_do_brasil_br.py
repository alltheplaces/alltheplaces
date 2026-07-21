import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.user_agents import BROWSER_DEFAULT

# Banco do Brasil's own point types (pontoTipo). Each is requested on its own: the server-side type filter
# keeps every response small enough to fetch through the proxy, and it excludes the shared "Banco 24 Horas"
# network (600) and third-party "Mais BB" correspondents (200), which are not BB-branded premises.
BANK_TYPES = ("101", "102", "104", "109")  # Agência BB, BB Estilo, BB Empresa, BB PAB
ATM_TYPE = "114"  # Sala de Autoatendimento (self-service ATM room)


class BancoDoBrasilBRSpider(Spider):
    name = "banco_do_brasil_br"
    item_attributes = {"brand": "Banco do Brasil", "brand_wikidata": "Q610817"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}  # Cloudflare serves an HTML challenge to non-browser UAs
    requires_proxy = "BR"  # Cloudflare also blocks data-centre IPs (CI fetch gets the challenge)

    async def start(self) -> AsyncIterator[Any]:
        # uf=todos returns a type nationwide in one response; tipoServico 0 = no service filter. The search
        # term is a required path segment (a brand/keyword token like "bb" yields an empty result), so a
        # locality name is used as the placeholder. Fetching one type per request keeps each response small.
        for poi_type in (*BANK_TYPES, ATM_TYPE):
            yield JsonRequest(
                url="https://www49.bb.com.br/encontreobb/rest/WsLocalizacaoAgencias/sao%20paulo/{}/0/?uf=todos".format(
                    poi_type
                )
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not isinstance(location, dict):
                continue
            item = DictParser.parse(location)  # maps latitude/longitude; BB's other fields use Portuguese keys
            item["lat"], item["lon"] = item["lat"].strip(), item["lon"].strip()  # source pads them with spaces
            item["ref"] = location["uor"]
            item["name"] = self.clean_name(location.get("nomePonto"))
            item["street_address"] = location.get("logradouro")
            item["city"] = location.get("municipio")
            item["state"] = location.get("descricaoUF")
            item["postcode"] = location.get("cep")
            item["opening_hours"] = self.parse_hours(location)
            if location["pontoTipo"] == ATM_TYPE:
                apply_category(Categories.ATM, item)  # standalone ATM room keeps its location label as name
            else:
                item["branch"] = item.pop("name")  # a branch label belongs in branch; NSI supplies the brand name
                apply_category(Categories.BANK, item)
            yield item

    @staticmethod
    def clean_name(name: str | None) -> str | None:
        # Self-service ATM rooms are prefixed with the "SAA" service tag (Sala de AutoAtendimento); drop it
        # and keep the real location label.
        return re.sub(r"^SAA[ -]", "", name or "").strip() or None

    def parse_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        # Weekday hours (dias úteis) apply Mo-Fr; Saturday and Sunday carry their own ranges. A 00:00-00:00
        # range means the point is closed that day.
        for days, start, end in (
            (DAYS_WEEKDAY, location.get("horaInicioDU"), location.get("horaFimDU")),
            (["Sa"], location.get("horaInicioSabado"), location.get("horaFimSabado")),
            (["Su"], location.get("horaInicioDomingo"), location.get("horaFimDoming")),
        ):
            if start and end and start != end:
                try:
                    oh.add_days_range(days, start, end)
                except ValueError:
                    pass
        return oh
