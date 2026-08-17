import html as html_module
import re
from typing import Any, Iterator

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

REF = re.compile(r"-(\d+)/?$")
ADDR = re.compile(r"EVgo EV Charging Station in (.+?)\s*\|")
STALLS = re.compile(r"There are (\d+) electric vehicle stalls")
H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)
TAGS = re.compile(r"<[^>]+>")

SOCKETS = {
    "CCS1": "socket:type1_combo",
    "CHAdeMO": "socket:chademo",
    "NACS": "socket:nacs",
    "J1772": "socket:type1",
}


def parse_site(url: str, page: str) -> dict[str, Any] | None:
    match = REF.search(url.split("?")[0])
    if not match:
        return None

    site: dict[str, Any] = {"ref": match.group(1), "website": url}

    if found := H1.search(page):
        site["name"] = html_module.unescape(TAGS.sub(" ", found.group(1))).replace("\xa0", " ").strip()

    if found := ADDR.search(page):
        site["addr_full"] = addr = html_module.unescape(found.group(1)).strip()
        parts = [part.strip() for part in addr.split(",")]
        if len(parts) >= 4:
            site["street_address"], site["city"] = parts[0], parts[1]
            site["state"] = parts[2].split()[0]

    if found := STALLS.search(page):
        site["capacity"] = found.group(1)

    site["sockets"] = sorted({key for label, key in SOCKETS.items() if label in page})
    return site


class EvgoUSSpider(SitemapSpider):
    name = "evgo_us"
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    sitemap_urls = ["https://www.evgo.com/find-a-charger/sites-sitemap.xml"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Iterator[Feature]:
        site = parse_site(response.url, response.text)
        if not site:
            self.crawler.stats.inc_value(f"atp/{self.name}/no_ref_in_url")
            return

        item = Feature()
        for field in ("ref", "website", "addr_full", "street_address", "city", "state"):
            item[field] = site.get(field)
        item["branch"] = site.get("name")
        if capacity := site.get("capacity"):
            item["extras"]["capacity"] = capacity
        for socket in site["sockets"]:
            item["extras"][socket] = "yes"

        apply_category(Categories.CHARGING_STATION, item)
        yield item
