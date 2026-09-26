import json
from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class FeuilletteFRSpider(Spider):
    name = "feuillette_fr"
    item_attributes = {"brand": "Boulangerie Feuillette", "brand_wikidata": "Q136205449"}
    allowed_domains = ["etablissements.groupe-feuillette.fr"]
    # robots.txt is behind the same Cloudflare challenge as the rest of the site.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        # Cloudflare bans Zyte's httpResponseBody here; only browserHtml gets through.
        yield Request(
            "https://etablissements.groupe-feuillette.fr/store-locator",
            meta={"zyte_api": {"browserHtml": True, "geolocation": "FR"}},
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        # The page embeds every Groupe Feuillette brand; the other brands are out of scope.
        for location in json.loads(response.xpath('//script[@id="etablissements-json"]/text()').get("")):
            if location.get("enseigne") != "Boulangerie Feuillette" or location.get("status") != "ouvert":
                continue

            item = Feature()
            item["ref"] = location["slug"]
            item["branch"] = (
                (location.get("nom") or "").removeprefix("Boulangerie Feuillette").strip().removeprefix("de ")
            )
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["street_address"] = location.get("adresse")
            item["city"] = location.get("ville")
            # Postcodes are JSON integers, so leading zeros are lost (e.g. 3400 for 03400).
            if postcode := location.get("codePostal"):
                item["postcode"] = str(postcode).zfill(5)
            item["phone"] = location.get("phone")
            item["website"] = f"https://etablissements.groupe-feuillette.fr/etablissement/{location['slug']}"

            if schedules := location.get("decodedSchedules"):
                item["opening_hours"] = OpeningHours()
                for period in schedules.get("periods", []):
                    if "close" in period:
                        item["opening_hours"].add_range(
                            DAYS_FROM_SUNDAY[period["open"]["day"]],
                            period["open"]["time"],
                            period["close"]["time"],
                            "%H%M",
                        )

            apply_category(Categories.SHOP_BAKERY, item)
            yield item
