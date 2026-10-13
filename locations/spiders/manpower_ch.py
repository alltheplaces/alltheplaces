from typing import Any, Iterable

from locations.storefinders.manpower_partoo import ManpowerPartooSpider


class ManpowerCHSpider(ManpowerPartooSpider):
    name = "manpower_ch"
    sitemap_urls = ["https://standorte.manpower.ch/de/sitemap.xml"]

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in super().sitemap_filter(entries):
            # The sitemap omits the language prefix, without which its pages are 404.
            entry["loc"] = entry["loc"].replace("manpower.ch/", "manpower.ch/de/")
            yield entry
