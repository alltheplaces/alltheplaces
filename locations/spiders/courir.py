import re
from typing import Any, Iterable

from scrapy.http import Request, Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class CourirSpider(SitemapSpider):
    name = "courir"
    item_attributes = {"brand": "Courir", "brand_wikidata": "Q3001258"}
    # The FR sitemap also covers BE, LU and MC; Spanish stores are only in the ES one.
    sitemap_urls = [
        "https://www.courir.com/fr/sitemap-custom-storeloc-fr.xml",
        "https://www.courir.es/es/sitemap-custom-storeloc-es.xml",
    ]
    sitemap_rules = [(r"/fr/magasin\?StoreID=\d+&format=json", "parse")]
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
            # Zyte gets a website ban on the JSON endpoints without these.
            request.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
            request.headers["X-Requested-With"] = "XMLHttpRequest"
            yield request

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        store = response.json()
        item = DictParser.parse(store)
        item["branch"] = re.sub(r"^COURIR\s+", "", item.pop("name", None) or "", flags=re.IGNORECASE)
        item["street_address"] = merge_address_lines([store.get("address1"), store.get("address2")])
        item["phone"] = store.get("phoneNumber")
        if item.get("country") == "ES":
            item["website"] = f"https://www.courir.es/es/tienda?StoreID={item['ref']}"
        else:
            item["website"] = f"https://www.courir.com/fr/magasin?StoreID={item['ref']}"

        if len(hours := store.get("openingHours") or []) == 7:
            item["opening_hours"] = OpeningHours()
            for day, ranges in zip(DAYS, hours):
                if not ranges:
                    item["opening_hours"].set_closed(day)
                for open_time, close_time in ranges:
                    item["opening_hours"].add_range(day, open_time, close_time)

        yield item
