import json
from typing import Any, AsyncIterator

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, DAYS_EN, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

COUNTRIES = {
    "FR": {
        "domain": "www.sephora.fr",
        "sfcc_site": "Sephora_FR",
        "locale": "fr_FR",
        "listing": "/magasin/",
    },
    "DE": {
        "domain": "www.sephora.de",
        "sfcc_site": "Sephora_DE",
        "locale": "de_DE",
        "listing": "/Stores-Alle/",
    },
    "IT": {
        "domain": "www.sephora.it",
        "sfcc_site": "Sephora_IT",
        "locale": "it_IT",
        "listing": "/beauty-store/",
    },
    "ES": {
        "domain": "www.sephora.es",
        "sfcc_site": "Sephora_ES",
        "locale": "es_ES",
        "listing": "/tiendas/",
    },
    "PT": {
        "domain": "www.sephora.pt",
        "sfcc_site": "Sephora_ES",
        "locale": "pt_PT",
        "listing": "/lojas/",
    },
    "PL": {
        "domain": "www.sephora.pl",
        "sfcc_site": "Sephora_PL",
        "locale": "pl_PL",
    },
    "CZ": {
        "domain": "www.sephora.cz",
        "sfcc_site": "Sephora_PL",
        "locale": "cs_CZ",
        "listing": "/prodejny",
    },
    "RO": {
        "domain": "www.sephora.ro",
        "sfcc_site": "Sephora_RO",
        "locale": "ro_RO",
        "listing": "/magazine",
    },
    "GR": {
        "domain": "www.sephora.gr",
        "sfcc_site": "Sephora_RO",
        "locale": "el_GR",
    },
    "SE": {
        "domain": "www.sephora.se",
        "sfcc_site": "Sephora_Scandinavia",
        "locale": "sv_SE",
        "listing": "/butiker/",
    },
    "DK": {
        "domain": "www.sephora.dk",
        "sfcc_site": "Sephora_Scandinavia",
        "locale": "da_DK",
    },
    "TR": {
        "domain": "www.sephora.com.tr",
        "sfcc_site": "Sephora_TR",
        "locale": "tr_TR",
        "listing": "/magazalar",
    },
}


class SephoraEuropeSpider(StructuredDataSpider):
    name = "sephora_europe"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        for country_code, config in COUNTRIES.items():
            domain = config["domain"]
            if "listing" in config:
                url = f"https://{domain}{config['listing']}"
            else:
                url = f"https://{domain}/on/demandware.store/Sites-{config['sfcc_site']}-Site/{config['locale']}/Stores-All"
            yield Request(url, callback=self.parse_listing, cb_kwargs={"country": country_code})

    def parse_listing(self, response: Response, country: str, **kwargs: Any) -> Any:
        store_links = response.xpath("//a[contains(@href, 'storeID')]/@href").getall()
        if not store_links:
            self.logger.warning("No store links found for %s at %s", country, response.url)
            return
        self.logger.info("Found %d stores for %s", len(store_links), country)
        for link in store_links:
            yield Request(response.urljoin(link), callback=self.parse_sd, meta={"country": country})

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item.pop("image", None)

        coord_data = response.xpath("//@data-coord").get()
        if coord_data:
            try:
                data = json.loads(coord_data)
                item["lat"] = data.get("lat")
                item["lon"] = data.get("lng")
            except (json.JSONDecodeError, TypeError):
                pass

        if ld_data.get("openingHours"):
            try:
                opening_hours = ld_data["openingHours"]
                hours_string = " ".join(opening_hours) if isinstance(opening_hours, list) else opening_hours
                item["opening_hours"] = OpeningHours()
                days = DAYS_CZ if response.meta.get("country") == "CZ" else DAYS_EN
                item["opening_hours"].add_ranges_from_string(hours_string, days=days)
            except Exception:
                self.logger.warning("Failed to parse opening hours for %s", response.url)

        item["country"] = response.meta.get("country")

        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("Sephora ").strip()

        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
