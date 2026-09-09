import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

BRAZIL_STATES = {
    "Acre": "AC",
    "Alagoas": "AL",
    "Amapá": "AP",
    "Amazonas": "AM",
    "Bahia": "BA",
    "Ceará": "CE",
    "Distrito Federal": "DF",
    "Espírito Santo": "ES",
    "Goiás": "GO",
    "Maranhão": "MA",
    "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG",
    "Pará": "PA",
    "Paraíba": "PB",
    "Paraná": "PR",
    "Pernambuco": "PE",
    "Piauí": "PI",
    "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Santa Catarina": "SC",
    "São Paulo": "SP",
    "Sergipe": "SE",
    "Tocantins": "TO",
}

# A generic fallback thumbnail served for any store that has no photo of
# its own, reused across roughly half of all locations.
PLACEHOLDER_IMAGE = "https://kopenhagen21.vteximg.com.br/arquivos/home-lista-imagem-02-item-04-min.png"


def clean(value: str) -> str | None:
    if value and value != "undefined":
        return value
    return None


class KopenhagenBRSpider(Spider):
    name = "kopenhagen_br"
    item_attributes = {"brand": "Kopenhagen", "brand_wikidata": "Q10314624", "name": "Kopenhagen"}
    allowed_domains = ["www.kopenhagen.com.br"]

    # The store finder widget is a private VTEX IO app
    # ("kopenhagen21.ourstores") that exposes a public GraphQL endpoint.
    # Requesting all ~800 stores in a single page times out server-side, so
    # results are paged the same way the widget itself pages them.
    page_size = 100
    query = """
        query allStores($page: Int, $pageSize: Int) @context(sender: "kopenhagen21.ourstores@4.0.3") {
          AllStores(page: $page, pageSize: $pageSize) {
            stores {
              id
              name
              image
              phoneNumber
              postalCode
              address
              number
              district
              city
              state
              latitude
              longitude
            }
            pagination {
              total
            }
          }
        }
    """

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.kopenhagen.com.br/_v/public/graphql/v1",
            data={"query": self.query, "variables": {"page": page, "pageSize": self.page_size}},
            cb_kwargs={"page": page},
        )

    def parse(self, response: Response, page: int, **kwargs: Any) -> Any:
        result = response.json()["data"]["AllStores"]

        for store in result["stores"]:
            feature = {
                "ref": store["id"],
                "street": clean(store.get("address")),
                "street-number": clean(store.get("number")) if clean(store.get("number")) != "0" else None,
                "city": clean(store.get("city")),
                "postal-code": self.clean_postcode(store.get("postalCode")),
                "lat": self.clean_coordinate(store.get("latitude")),
                "lon": self.clean_coordinate(store.get("longitude")),
                "phone": clean(store.get("phoneNumber")),
            }
            item = DictParser.parse(feature)
            item["branch"] = re.sub(r"^KO[KP]\s+", "", store["name"], flags=re.IGNORECASE).title()
            item["state"] = BRAZIL_STATES.get(store.get("state"), store.get("state"))
            item["country"] = "BR"

            if district := clean(store.get("district")):
                item["extras"]["addr:suburb"] = district.title()

            if (image := clean(store.get("image"))) and image != PLACEHOLDER_IMAGE:
                item["image"] = image

            apply_category(Categories.SHOP_CHOCOLATE, item)

            yield item

        if page * self.page_size < result["pagination"]["total"]:
            yield self.make_request(page + 1)

    @staticmethod
    def clean_coordinate(value: str) -> str | None:
        # A small number of records have stray non-numeric characters
        # (e.g. a trailing comma or letter) tacked onto an otherwise valid
        # coordinate; strip these rather than discarding the coordinate.
        if value and (match := re.match(r"-?\d+\.\d+", value)):
            return match.group(0)
        return value

    @staticmethod
    def clean_postcode(postcode: str) -> str | None:
        if not (digits := re.sub(r"\D", "", postcode or "")):
            return None
        # A meaningful share of postcodes are missing their leading zero.
        digits = digits.zfill(8)
        return f"{digits[:5]}-{digits[5:]}"
