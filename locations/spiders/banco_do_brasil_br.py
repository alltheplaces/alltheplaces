import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.user_agents import BROWSER_DEFAULT

API_BASE = "https://encontre-bb-api.bb.com.br/ws-localizacao-agencias"
# Banco do Brasil's own point types (tipoPonto): Agência BB, BB Estilo, BB Empresa, BB PAB and Sala de
# Autoatendimento (self-service ATM room). This excludes the shared "Banco 24 Horas" network (600) and
# third-party "Mais BB" correspondents (200), which are not BB-branded premises.
POINT_TYPES = "101,102,104,109,114"
ATM_TYPE = 114
SHARED_HOTLINE = 40033001


class BancoDoBrasilBRSpider(Spider):
    name = "banco_do_brasil_br"
    item_attributes = {"brand": "Banco do Brasil", "brand_wikidata": "Q610817"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}  # Cloudflare serves an HTML challenge to non-browser UAs
    requires_proxy = "BR"  # Cloudflare also blocks data-centre IPs (CI fetch gets the challenge)

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url=f"{API_BASE}/todosOsPontos/{POINT_TYPES}/0?page=1&limit=1000")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for location in data["pontosAtendimento"]:
            item = DictParser.parse(location)  # maps latitude/longitude; BB's other fields use Portuguese keys
            item["lat"], item["lon"] = item["lat"].strip(), item["lon"].strip()  # source pads them with spaces
            item["ref"] = location["uor"]
            item["name"] = self.clean_name(location.get("nm_ponto"))
            item["street_address"] = ", ".join(filter(None, [location.get("logradouro"), location.get("complemento")]))
            item["city"] = location.get("municipio")
            item["state"] = location.get("uf")
            item["postcode"] = str(location["cep"]) if location.get("cep") else None
            if location.get("telefone") and location["telefone"] != SHARED_HOTLINE and location.get("ddd_telefone"):
                item["phone"] = "+55 {} {}".format(location["ddd_telefone"], location["telefone"])
            item["opening_hours"] = self.parse_hours(location)
            if location["tipoPonto"] == ATM_TYPE:
                apply_category(Categories.ATM, item)  # standalone ATM room keeps its location label as name
            else:
                item["branch"] = item.pop("name")  # a branch label belongs in branch; NSI supplies the brand name
                apply_category(Categories.BANK, item)
            yield item

        if next_page := data.get("meta", {}).get("next"):
            yield JsonRequest(url=API_BASE + next_page)

    @staticmethod
    def clean_name(name: str | None) -> str | None:
        # Self-service ATM rooms are prefixed with the "SAA" service tag (Sala de AutoAtendimento) and
        # agencies with their numeric agency code; drop both and keep the real location label.
        return re.sub(r"^(SAA[ -]|\d+ - )", "", name or "").strip() or None

    def parse_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        # Weekday hours apply Mo-Fr; Saturday and Sunday carry their own ranges. An identical start and end
        # (00:00-00:00) means the point is closed that day.
        for days, start, end in (
            (DAYS_WEEKDAY, location.get("atdt_hr_ini"), location.get("atdt_hr_fim")),
            (["Sa"], location.get("sabado_hr_ini"), location.get("sabado_hr_fim")),
            (["Su"], location.get("domingo_hr_ini"), location.get("domingo_hr_fim")),
        ):
            if not start or not end:
                continue
            if start == end:
                oh.set_closed(days)
            else:
                oh.add_days_range(days, start, end, time_format="%H:%M:%S")
        return oh
