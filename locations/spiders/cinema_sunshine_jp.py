import re
from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

AREA_URL = "https://www.cinemasunshine.co.jp/areas/"
STATE_JS_RE = re.compile(r"/_nuxt/static/(\d+)/areas/state\.js")
SLUG_RE = re.compile(r'href="/theater/([a-z0-9]+)/"')
COORD_RE = re.compile(r"!2d([-\d.]+)!3d([-\d.]+)")
POSTCODE_RE = re.compile(r"〒\s*(\d{3})-?(\d{4})")
PHONE_RE = re.compile(r"\d{2,5}-\d{2,4}-\d{3,4}")

PARAMS_RE = re.compile(r"function\(([\w_$,]+)\)")
VALUES_RE = re.compile(r"}\((.+)\)\)\);")
OBJECT_RE = re.compile(r"return (\{.*)}\(", re.DOTALL)


def parse_nuxt_jsonp(text: str) -> dict:
    """Parse a Nuxt static JSONP payload.

    Nuxt hoists repeated strings into the anonymous function's arguments, so
    the object literal alone yields placeholders. splice the real values back
    in via the params to args map.
    """
    params = PARAMS_RE.search(text).group(1).split(",")
    values = chompjs.parse_js_object(f"[{VALUES_RE.search(text).group(1)}]")
    data_object = chompjs.parse_js_object(OBJECT_RE.search(text).group(1))
    args = dict(zip(params, values))
    payload = _populate_placeholders(data_object, args)
    return payload


def _populate_placeholders(data: Any, args: dict[str, Any]) -> Any:
    """Replace minified placeholder strings with their real values."""
    if isinstance(data, str):
        return args.get(data, data)
    elif isinstance(data, list):
        return [_populate_placeholders(value, args) for value in data]
    elif isinstance(data, dict):
        return {key: _populate_placeholders(value, args) for key, value in data.items()}
    return data


class CinemaSunshineJPSpider(JSONBlobSpider):
    name = "cinema_sunshine_jp"
    item_attributes = {"brand": "シネマサンシャイン", "brand_wikidata": "Q11307419"}
    start_urls = [AREA_URL]

    def parse(self, response: Response, **kwargs):
        if "payload.js" in response.url:
            yield from super().parse(response)
            return
        for slug in SLUG_RE.findall(response.text):
            yield scrapy.Request(url=self.build_nuxt_payload_url(response, slug), callback=self.parse)

    @staticmethod
    def build_nuxt_payload_url(response: Response, slug: str) -> str:
        build_id = STATE_JS_RE.search(response.text).group(1)
        return f"https://www.cinemasunshine.co.jp/_nuxt/static/{build_id}/theater/{slug}/access/payload.js"

    def extract_json(self, response: Response) -> list[dict]:
        payload = parse_nuxt_jsonp(response.text)
        return [payload["data"][0]["theater"]["attributes"]]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Any:
        item["ref"] = feature["path"]
        item["branch"] = item.pop("name", "")
        item["name"] = "シネマサンシャイン"
        item["country"] = "JP"

        if coords := self.extract_coords(feature.get("google_map_url") or ""):
            item["lat"], item["lon"] = coords

        accesses = {acc.get("name"): acc.get("value") for acc in feature.get("accesses") or []}
        if address_raw := accesses.get("住所"):
            address_cleaned = " ".join(address_raw.split("\n")[0].replace("\u3000", " ").split())
            item["addr_full"] = POSTCODE_RE.sub("", address_cleaned).strip()
        if phone := accesses.get("電話番号"):
            if phone_match := PHONE_RE.search(phone):
                item["phone"] = f"+81 {phone_match.group(0)}"

        if screens := feature.get("screens"):
            item["extras"]["screen"] = str(len(screens))
            if any("IMAX" in (screen.get("name") or "") for screen in screens):
                apply_yes_no("cinema:IMAX", item, True)

        apply_category(Categories.CINEMA, item)
        yield item

    @staticmethod
    def extract_coords(url: str) -> tuple[float, float] | None:
        if coord := COORD_RE.search(url):
            return float(coord.group(2)), float(coord.group(1))
        return None
