import html as html_module
import re
from typing import Any, AsyncIterator, Iterable, Iterator

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT

BASE = "https://www.evgo.com"
STATES_SITEMAP = f"{BASE}/find-a-charger/states-sitemap.xml"

STATES = (
    "al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt "
    "ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy"
).split()

SITE_HREF = re.compile(
    r"""href=["'](?:https?://(?:www\.)?evgo\.com)?(/find-a-charger/[a-z]{2}/[^/"'?#]+/[^/"'?#]+/?)["']"""
)

REF = re.compile(r"-(\d+)/?$")

SITE_PATH = re.compile(r"/find-a-charger/([a-z]{2})/([^/]+)/(.+?)/?$")

STATE_URL = re.compile(r"""https?://(?:www\.)?evgo\.com/find-a-charger/([a-z]{2})/?(?=["'<\s]|$)""")

STATIC_MAP_CENTRE = re.compile(
    r"maps\.googleapis\.com/maps/api/staticmap\?[^\"'\s]*?center=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"
)

STALLS = (
    re.compile(r"There are (\d+) electric vehicle stalls"),
    re.compile(r"""title=["'](\d+) stalls at this location["']"""),
    re.compile(r">\s*(\d+) stalls\s*<"),
)

TITLE_ADDR = re.compile(r"EVgo EV Charging Station in (.+?)\s*\|")

H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)
TAGS = re.compile(r"<[^>]+>")
POWER_KW = re.compile(r"(\d{2,3})\s*kW")

SOCKETS = {
    "CCS1": "socket:type1_combo",
    "CHAdeMO": "socket:chademo",
    "NACS": "socket:nacs",
    "J1772": "socket:type1",
}


def _text(fragment: str) -> str:
    """Strip tags and unescape entities from a captured HTML fragment."""
    return html_module.unescape(TAGS.sub(" ", fragment)).replace("\xa0", " ").strip()


def _first(patterns: Iterable[re.Pattern], text: str) -> str | None:
    for pattern in patterns:
        if match := pattern.search(text):
            return match.group(1)
    return None


def site_urls(page_html: str) -> list[str]:
    seen = {}
    for path in SITE_HREF.findall(page_html):
        seen.setdefault("/" + path.strip("/") + "/", None)
    return [BASE + path for path in seen]


def parse_site(url: str, page_html: str) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {"website": url}
    problems: list[str] = []

    if match := REF.search(url.split("?")[0]):
        data["ref"] = match.group(1)
    else:
        problems.append("ref: no trailing site id in the URL slug")

    if match := SITE_PATH.search(url.split("?")[0]):
        state, city, slug = match.groups()
        data["state"] = state.upper()
        data["city"] = city.replace("-", " ").title()
        data["street_address"] = slug.rsplit("-", 1)[0].replace("-", " ").title()

    if match := STATIC_MAP_CENTRE.search(page_html):
        data["lat"], data["lon"] = float(match.group(1)), float(match.group(2))
    else:
        problems.append("coordinates: no Google static map URL in og:image")

    if match := TITLE_ADDR.search(page_html):
        data["addr_full"] = html_module.unescape(match.group(1)).strip()
        parts = [p.strip() for p in data["addr_full"].split(",")]
        if len(parts) >= 4:
            data["street_address"] = parts[0]
            data["city"] = parts[1]
    else:
        problems.append("addr_full: page title did not match the expected wording")

    if match := H1.search(page_html):
        data["name"] = _text(match.group(1))
    if not data.get("name"):
        problems.append("name: no <h1> on the page")

    if stalls := _first(STALLS, page_html):
        data["capacity"] = int(stalls)
    else:
        problems.append("capacity: no stall count in og:description or body")

    if powers := [int(kw) for kw in POWER_KW.findall(page_html)]:
        data["output_kw"] = max(powers)

    data["sockets"] = sorted({key for label, key in SOCKETS.items() if label in page_html})
    if not data["sockets"]:
        problems.append("sockets: no connector labels found")

    return data, problems


def state_codes(sitemap_body: str) -> list[str]:
    """State codes linked from states-sitemap.xml, in file order."""
    return list(dict.fromkeys(STATE_URL.findall(sitemap_body)))

class EvgoUSSpider(PlaywrightSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    allowed_domains = ["evgo.com"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "USER_AGENT": BROWSER_DEFAULT,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 1.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "RETRY_TIMES": 5,
        "RETRY_HTTP_CODES": [408, 429, 500, 502, 503, 504, 522, 524],
        "DOWNLOAD_TIMEOUT": 60,
    }

    def _browser_request(self, url: str, callback, **kwargs) -> Request:
        return Request(url, callback=callback, meta={"playwright": True}, **kwargs)

    async def start(self) -> AsyncIterator[Request]:
        yield self._browser_request(STATES_SITEMAP, self.parse_states, errback=self.states_failed)

    def parse_states(self, response: Response) -> Iterable[Request]:
        codes = state_codes(response.text)
        if not codes:
            self.logger.error(
                "states-sitemap.xml held no state pages. First 300 chars: {}".format(response.text[:300])
            )
            self.crawler.stats.inc_value(f"atp/{self.name}/states_sitemap_empty")
            yield from self.fallback_states()
            return
        self.crawler.stats.set_value(f"atp/{self.name}/states_found", len(codes))
        if missing := sorted(set(STATES) - set(codes)):
            self.logger.warning("states-sitemap.xml is missing {}".format(", ".join(missing)))
        for code in codes:
            yield self._browser_request(f"{BASE}/find-a-charger/{code}/", self.parse_state)

    def states_failed(self, failure) -> Iterable[Request]:
        self.logger.error("states-sitemap.xml unreachable ({}), falling back to the built-in state list".format(failure.value))
        self.crawler.stats.inc_value(f"atp/{self.name}/states_sitemap_unreachable")
        yield from self.fallback_states()

    def fallback_states(self) -> Iterable[Request]:
        for code in STATES:
            yield self._browser_request(f"{BASE}/find-a-charger/{code}/", self.parse_state)

    def parse_state(self, response: Response) -> Iterable[Request]:
        urls = site_urls(response.text)
        if not urls:
            self.logger.warning("no site links on {}".format(response.url))
            self.crawler.stats.inc_value(f"atp/{self.name}/state_page_empty")
            return
        self.crawler.stats.inc_value(f"atp/{self.name}/sites_linked", len(urls))
        for url in urls:
            yield self._browser_request(url, self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Iterator[Feature]:
        if response.url.strip("/").endswith("find-a-charger"):
            return

        data, problems = parse_site(response.url, response.text)
        for problem in problems:
            self.crawler.stats.inc_value(f"atp/{self.name}/missing/{problem.split(':')[0]}")

        if "ref" not in data or "lat" not in data:
            self.logger.warning("dropped {}: {}".format(response.url, "; ".join(problems)))
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped")
            return

        item = Feature()
        item["ref"] = data["ref"]
        item["website"] = data["website"]
        item["branch"] = data.get("name")
        item["addr_full"] = data.get("addr_full")
        item["street_address"] = data.get("street_address")
        item["city"] = data.get("city")
        item["state"] = data.get("state")
        item["lat"], item["lon"] = data["lat"], data["lon"]

        if capacity := data.get("capacity"):
            item["extras"]["capacity"] = str(capacity)
        if output := data.get("output_kw"):
            item["extras"]["charging_station:output"] = f"{output} kW"
        for socket in data["sockets"]:
            item["extras"][socket] = "yes"

        apply_category(Categories.CHARGING_STATION, item)
        yield item
