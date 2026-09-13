import re
from typing import Any, AsyncIterator

import xmltodict
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class CaixabankESSpider(Spider):
    name = "caixabank_es"
    item_attributes = {"brand": "Caixabank", "brand_wikidata": "Q847225"}

    # The locator returns up to 200 points per bounding box (in "detail" mode, only reached at zoom>=13,
    # regardless of the box's actual size), so Spain's extent is searched recursively: any box that hits
    # the cap is split into quadrants (DuplicatesPipeline drops overlaps by ref).
    max_results = 200

    def bbox_request(self, lat1: float, lat2: float, lon1: float, lon2: float) -> Request:
        return Request(
            url=(
                "https://www4.caixabank.es/aplnr/caixamaps/index_en.html"
                f"?tipoCentro=oficinas,centroCajeros&servicios=&zoom=13"
                f"&latMin={lat1}&latMax={lat2}&longMin={lon1}&longMax={lon2}"
            ),
            cb_kwargs={"bbox": (lat1, lat2, lon1, lon2)},
        )

    async def start(self) -> AsyncIterator[Request]:
        # Covers mainland Spain, the Balearic and Canary Islands, and Ceuta/Melilla
        yield self.bbox_request(27.0, 44.0, -18.5, 4.5)

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        # Some names contain a literal unescaped "&" (e.g. "Touristic Train & Tuk Tuk Tene"), which makes
        # the response invalid XML; escape any bare ampersand that isn't already part of an entity/charref.
        xml_text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", response.text)
        centros = xmltodict.parse(xml_text).get("centros") or {}
        items = centros.get("centro") or []
        if isinstance(items, dict):  # xmltodict collapses a single result to a dict, not a list
            items = [items]

        if len(items) >= self.max_results:  # cap hit: subdivide into quadrants; the leaf cells return the points
            lat1, lat2, lon1, lon2 = bbox
            lat_mid, lon_mid = (lat1 + lat2) / 2, (lon1 + lon2) / 2
            yield self.bbox_request(lat1, lat_mid, lon1, lon_mid)
            yield self.bbox_request(lat1, lat_mid, lon_mid, lon2)
            yield self.bbox_request(lat_mid, lat2, lon1, lon_mid)
            yield self.bbox_request(lat_mid, lat2, lon_mid, lon2)
            return

        for centro in items:
            yield from self.parse_centro(centro)

    def parse_centro(self, centro: dict) -> Any:
        tipo = centro.get("@tipo")
        if tipo not in ("oficina", "centroCajeros"):
            return

        loc = centro.get("localizacion") or {}
        name = re.sub(r"\s{2,}", " ", centro.get("nombre") or "").strip() or None
        item = Feature(
            ref=centro.get("@codigo"),
            name=name,
            street_address=centro.get("direccion"),
            city=centro.get("localidad"),
            postcode=centro.get("codigoPostal"),
            lat=loc.get("@latitude"),
            lon=loc.get("@longitude"),
        )
        # "telefono" is a single national hotline (+34 600 40 40 90) repeated identically across every
        # branch, not a branch-specific line, so it is intentionally not used here.
        if url_seo := centro.get("urlSeo"):
            item["website"] = "https://www4.caixabank.es" + url_seo

        if tipo == "oficina":
            item["branch"] = item.pop("name")
            apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.ATM, item)

        yield item
