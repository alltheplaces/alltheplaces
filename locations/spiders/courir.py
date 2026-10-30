import re
from datetime import datetime
from typing import Any, Iterable

from scrapy.http import Request, Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class CourirSpider(SitemapSpider):
    name = "courir"
    item_attributes = {"brand": "Courir", "brand_wikidata": "Q3001258", "name": "Courir"}
    # The FR sitemap covers FR, BE, LU and MC; most Spanish stores are only in the ES one.
    sitemap_urls = [
        "https://www.courir.com/fr/sitemap-custom-storeloc-fr.xml",
        "https://www.courir.es/es/sitemap-custom-storeloc-es.xml",
    ]
    # Datacenter IPs get a 403 on every GET.
    requires_proxy = "FR"
    custom_settings = {"ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"]}

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            if m := re.search(r"StoreID=(\d+)", entry["loc"]):
                # The store page answers with JSON for any store, including Spanish ones.
                entry["loc"] = f"https://www.courir.com/fr/magasin?StoreID={m.group(1)}&format=json&ajax=true"
                yield entry

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            if request.callback == self.parse:
                # Zyte gets a website ban on the JSON endpoints without these.
                request.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
                request.headers["X-Requested-With"] = "XMLHttpRequest"
            yield request

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        store = response.json()
        item = DictParser.parse(store)
        if m := re.match(r"(?:COURIR\s+)?(OUTLET\s+)?(.+)", item.pop("name", None) or "", flags=re.IGNORECASE):
            item["branch"] = m.group(2)
            if m.group(1):
                item["name"] = "Courir Outlet"
        item["street_address"] = merge_address_lines([store.get("address1"), store.get("address2")])
        # The source tags the Monaco store as FR.
        if item.get("country") == "FR" and (item.get("postcode") or "").startswith("980"):
            item["country"] = "MC"
        if item.get("country") == "ES":
            item["website"] = f"https://www.courir.es/es/tienda?StoreID={item['ref']}"
        else:
            item["website"] = f"https://www.courir.com/fr/magasin?StoreID={item['ref']}"

        # Closures are only stated in this free-text note.
        note = store.get("informations") or ""
        if re.search(r"d[ée]finitivement|definitivamente", note, flags=re.IGNORECASE):
            set_closed(item)
        elif m := re.search(r"Fermeture d[ée]finitive le (\d{2}\.\d{2}\.\d{4})", note, flags=re.IGNORECASE):
            try:
                set_closed(item, datetime.strptime(m.group(1), "%d.%m.%Y"))
            except ValueError:
                set_closed(item)

        # Closed stores leave every day empty: that means unknown hours, not closed all week.
        if len(hours := store.get("openingHours") or []) == 7 and any(hours):
            item["opening_hours"] = OpeningHours()
            for day, ranges in zip(DAYS, hours):
                if not ranges:
                    item["opening_hours"].set_closed(day)
                for open_time, close_time in ranges:
                    item["opening_hours"].add_range(day, open_time, close_time)

        # NSI's Courir entry doesn't cover Monaco.
        apply_category(Categories.SHOP_SHOES, item)
        yield item
