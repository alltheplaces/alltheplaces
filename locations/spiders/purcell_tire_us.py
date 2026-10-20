import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The all-locations page is built with the Divi page builder: each location is a
# column holding the city and service type, the address and phone, and a
# Google Maps embed whose URL carries the coordinates.
#
# Locations have a service type. Tyre shops ("Commercial", "Consumer",
# "Commercial & Consumer", "Truck Tire Center") are tagged as shops, and the
# distribution centres as warehouses. Retread plants are industrial sites
# rather than shops, and are skipped.
#
# No opening hours are published on this page.
#
# No brand:wikidata is set because the chain has no Wikidata item.

WAREHOUSES = {"Distribution Services", "Central Distribution"}
SKIPPED = {"Retread"}


class PurcellTireUSSpider(Spider):
    name = "purcell_tire_us"
    item_attributes = {"brand": "Purcell Tire"}
    allowed_domains = ["purcelltire.com"]
    start_urls = ["https://purcelltire.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.xpath(
            '//div[contains(@class, "et_pb_column_1_4")][.//iframe[contains(@src, "maps/embed")]]'
        ):
            service = re.sub(r"\s+", " ", location.xpath(".//h2/text()").get("")).strip()
            if service in SKIPPED:
                continue

            item = Feature()
            item["website"] = location.xpath('.//a[contains(@href, "/store-")]/@href').get()
            item["ref"] = (item["website"] or "").rstrip("/").rsplit("/", 1)[-1] or None
            item["branch"] = location.xpath(".//h2/preceding-sibling::p[1]/text()").get("").strip()
            item["phone"] = location.xpath(".//h4/text()").get()

            lines = self.address_lines(location.xpath(".//h4/preceding-sibling::p[1]//text()").getall())
            # Usually "342 Chipperfield Dr" / "Anchorage, AK 99501", but a few
            # locations put the whole address on one line.
            if lines and (locality := re.fullmatch(r"(.+?),\s*([A-Z]{2})\s+(\d{5})", lines[-1])):
                item["city"], item["state"], item["postcode"] = locality.groups()
                item["street_address"] = ", ".join(lines[:-1])
            elif address := re.fullmatch(r"(.*?),\s*([^,]+?),?\s+([A-Z]{2}),?\s+(\d{5})", ", ".join(lines)):
                item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
            else:
                item["addr_full"] = ", ".join(lines)

            embed = location.xpath('.//iframe[contains(@src, "maps/embed")]/@src').get("")
            if coordinates := re.search(r"!2d(-?[\d.]+)!3d(-?[\d.]+)", embed):
                item["lon"], item["lat"] = coordinates.groups()

            if service in WAREHOUSES:
                apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
            else:
                apply_category(Categories.SHOP_TYRES, item)

            yield item

    @staticmethod
    def address_lines(nodes: list[str]) -> list[str]:
        """
        The address is split into text nodes inconsistently: commas, state
        codes and postcodes sometimes sit in a node of their own, so those are
        stitched back onto the line before them.
        """
        lines = []
        for node in nodes:
            line = re.sub(r"\s+", " ", node).strip()
            if not line:
                continue
            if lines and (line.startswith(",") or lines[-1].endswith(",") or re.fullmatch(r"[A-Z]{2}", line)):
                lines[-1] = f"{lines[-1].rstrip(', ')}, {line.lstrip(', ')}"
            elif lines and re.fullmatch(r"\d{5}", line) and re.search(r"[A-Z]{2}$", lines[-1]):
                lines[-1] = f"{lines[-1]} {line}"
            else:
                lines.append(line)
        return lines
