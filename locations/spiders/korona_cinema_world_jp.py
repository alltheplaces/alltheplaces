import re
from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import clean_facebook, clean_instagram, clean_twitter

AREA_URL = "https://cinema.korona.co.jp/areas/"
STATE_JS_RE = re.compile(r"/_nuxt/static/(\d+)/areas/state\.js")
CODE_RE = re.compile(r"/theaters/([a-z]{3})/")
POSTCODE_RE = re.compile(r"(\d{3}-\d{4})")
TIME_RE = re.compile(r"(\d{1,2})[：:](\d{2})[~～](\d{1,2})[：:](\d{2})")

PARAMS_RE = re.compile(r"function\(([\w_$,]+)\)")
# Nuxt hoists repeated strings into the anonymous function's arguments, so the
# returned object holds placeholder identifiers. The argument list is the last
# top-level parenthesised group closing the payload; a string-aware pattern is
# used because the argument values contain parens inside strings.
VALUES_INNER_RE = r'(?:\\.|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^("\'\\])*'
VALUES_RE = re.compile(r"\(\s*(" + VALUES_INNER_RE + r")\)\)\);$", re.DOTALL)
OBJECT_RE = re.compile(r"return\s+(\{)")


def parse_nuxt_jsonp(text: str) -> dict:
    """Parse a Nuxt static JSONP payload.

    The returned object and its placeholder arguments are extracted with
    regexes and parsed with chompjs, then the real values are spliced back in
    via the params to args map. The object's closing brace sits two characters
    before the argument list's opening parenthesis (the function-body brace
    and the object's own brace), so no balanced matching is required.
    """
    params = PARAMS_RE.search(text).group(1).split(",")

    args_match = VALUES_RE.search(text)
    values = chompjs.parse_js_object(f"[{args_match.group(1)}]")

    obj_open = OBJECT_RE.search(text).start(1)
    obj_close = args_match.start() - 2
    data_object = chompjs.parse_js_object(text[obj_open : obj_close + 1])

    arg_map = dict(zip(params, values))
    return _populate_placeholders(data_object, arg_map)


def _populate_placeholders(data: Any, args: dict[str, Any]) -> Any:
    """Replace minified placeholder strings with their real values."""
    if isinstance(data, str):
        return args.get(data, data)
    elif isinstance(data, list):
        return [_populate_placeholders(value, args) for value in data]
    elif isinstance(data, dict):
        return {key: _populate_placeholders(value, args) for key, value in data.items()}
    return data


class KoronaCinemaWorldJPSpider(JSONBlobSpider):
    name = "korona_cinema_world_jp"
    item_attributes = {
        "brand": "コロナシネマワールド",
        "brand_wikidata": "Q11302883",
        "extras": {"brand:en": "Corona Cinema World", "brand:ja": "コロナシネマワールド"},
    }
    start_urls = [AREA_URL]

    def parse(self, response: Response, **kwargs):
        if "payload.js" in response.url:
            yield from super().parse(response)
            return
        build_id = STATE_JS_RE.search(response.text).group(1)
        for code in sorted(set(CODE_RE.findall(response.text))):
            yield scrapy.Request(
                url=f"https://cinema.korona.co.jp/_nuxt/static/{build_id}/theaters/{code}/payload.js",
                callback=self.parse,
            )

    def extract_json(self, response: Response) -> list[dict]:
        payload = parse_nuxt_jsonp(response.text)
        return [payload["data"][0]["theater"]["attributes"]]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Any:
        item["ref"] = feature["path"]
        item["branch"] = item.pop("name", "")
        item["name"] = "コロナシネマワールド"
        item["website"] = f"https://cinema.korona.co.jp/theaters/{feature['path']}/"
        item["country"] = "JP"

        if coords := url_to_coords(feature.get("google_map_url") or ""):
            item["lat"], item["lon"] = coords

        accesses = {acc.get("name"): acc.get("value") for acc in feature.get("accesses") or []}
        if phone := accesses.get("電話番号"):
            item["phone"] = f"+81 {phone.splitlines()[0].strip()}"
        if address := accesses.get("住所"):
            address = address.replace("\u3000", " ").replace("\n", " ").strip()
            if match := POSTCODE_RE.match(address):
                item["postcode"] = match.group(1)
                address = address[match.end() :].strip()

            item["addr_full"] = address

        self.apply_opening_hours(item, feature.get("opening_hours") or [])
        self.apply_socials(item, feature.get("sns_list") or [])

        if screens := feature.get("screens") or []:
            item["extras"]["screen"] = str(len(screens))

        apply_category(Categories.CINEMA, item)
        yield item

    DAY_RULES = {
        "平日": {"days": DAYS[:5]},
        "土曜日": {"days": ["Sa"]},
        "日・祝日": {"days": ["Su"], "holiday": "PH"},
        "月曜日～木曜日": {"days": DAYS[:4]},
        "金曜日": {"days": ["Fr"]},
        "金曜日・祝前日": {"days": ["Fr"], "holiday": "PH -1 day"},
        "金曜日～日曜日・祝日": {"days": DAYS[4:], "holiday": "PH"},
    }

    def apply_opening_hours(self, item: Feature, rows: list) -> None:
        oh = OpeningHours()
        holiday_clauses = []
        for row in rows:
            if not (match := TIME_RE.search(row["opening_hours"])):
                continue
            label = row["opening_hours"][: match.start()].strip()
            rule = self.DAY_RULES.get(label)
            if not rule:
                self.logger.warning(f"Unhandled opening hours label for {item.get('ref')}: {label!r}")
                continue
            open_time = f"{int(match.group(1)):02d}:{match.group(2)}"
            close_time = f"{int(match.group(3)):02d}:{match.group(4)}"
            oh.add_days_range(rule["days"], open_time, close_time)
            if prefix := rule.get("holiday"):
                holiday_clauses.append(f"{prefix} {open_time}-{close_time}")
        if hours := oh.as_opening_hours():
            if holiday_clauses:
                hours += "; " + "; ".join(holiday_clauses)
            item["opening_hours"] = hours

    def apply_socials(self, item: Feature, sns_list: list) -> None:
        for sns in sns_list:
            url = sns.get("url") or ""
            identifier = (sns.get("identifier") or "").upper()
            if "LINE" in identifier:
                item["extras"]["contact:line"] = url
            elif "X" in identifier or "TWITTER" in identifier:
                if twitter := clean_twitter(url):
                    item["twitter"] = twitter
            elif "FACEBOOK" in identifier:
                if facebook := clean_facebook(url):
                    item["facebook"] = facebook
            elif "INSTA" in identifier:
                if instagram := clean_instagram(url):
                    item["extras"]["contact:instagram"] = instagram
