from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KontantenDKSpider(Spider):
    name = "kontanten_dk"
    item_attributes = {"brand": "Kontanten", "brand_wikidata": "Q126902178"}
    start_urls = ["https://www.nokas.dk/produkter/kontanten/"]

    # Data is parsed from HTML attributes/elements, not a JSON blob, so DictParser is not used.
    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Match the "atm" class as a whole token: excludes døgnboks deposit boxes and
        # "kommende-atmer" (upcoming, not-yet-operational) locations. A bare contains() would
        # leak the latter in, since "atm" is a substring of "atmer".
        for location in response.xpath(
            '//*[contains(@class, "map-list-page__locations__location") and contains(concat(" ", normalize-space(@class), " "), " atm ")]'
        ):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["branch"] = (
                location.xpath('.//*[contains(@class, "map-list-page__locations__location__heading")]/text()').get()
                or ""
            ).replace("KONTANTEN ", "").strip() or None
            item["addr_full"] = location.xpath(
                './/*[contains(@class, "map-list-page__locations__location__heading")]/following-sibling::p[1]/text()'
            ).get()
            apply_category(Categories.ATM, item)
            yield item
