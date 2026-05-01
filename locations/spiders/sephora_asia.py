import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

COUNTRIES = {
    "SG": "www.sephora.sg",
    "MY": "www.sephora.my",
    "TH": "www.sephora.co.th",
    "ID": "www.sephora.co.id",
    "HK": "www.sephora.hk",
    "AU": "www.sephora.com.au",
    "NZ": "www.sephora.nz",
}


class SephoraAsiaSpider(Spider):
    name = "sephora_asia"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        for cc, domain in COUNTRIES.items():
            yield Request(f"https://{domain}/store-locations", cb_kwargs={"country": cc, "domain": domain})

    def parse(self, response: Response, country: str, domain: str, **kwargs: Any) -> Any:
        nuxt_data = response.xpath('//script[@id="__NUXT_DATA__"]/text()').get()
        if not nuxt_data:
            self.logger.warning("No Nuxt data found for %s", country)
            return

        payload = json.loads(nuxt_data)

        for entry in payload:
            if not isinstance(entry, dict) or "storeLocationCardProps" not in entry:
                continue
            cards_idx = entry["storeLocationCardProps"]
            if not isinstance(cards_idx, int) or cards_idx >= len(payload):
                continue
            card_indices = payload[cards_idx]
            if not isinstance(card_indices, list):
                continue
            for ci in card_indices:
                if not isinstance(ci, int) or ci >= len(payload):
                    continue
                card = payload[ci]
                if isinstance(card, dict):
                    yield from self._parse_store(payload, card, country, domain)

    def _resolve(self, payload: list, value: Any) -> Any:
        if isinstance(value, int) and value < len(payload):
            return payload[value]
        return value

    def _parse_store(self, payload: list, card: dict, country: str, domain: str) -> Any:
        store_id = self._resolve(payload, card.get("id"))
        name = self._resolve(payload, card.get("name"))
        address = self._resolve(payload, card.get("address"))
        phone = self._resolve(payload, card.get("phone"))
        hours_text = self._resolve(payload, card.get("hours"))
        slug = self._resolve(payload, card.get("slugUrl"))

        item = Feature()
        item["ref"] = store_id
        item["branch"] = name
        item["street_address"] = address
        item["phone"] = phone

        cta = self._resolve(payload, card.get("cta"))
        if isinstance(cta, dict):
            map_url = self._resolve(payload, cta.get("mapUrl"))
            if isinstance(map_url, str):
                coords = url_to_coords(map_url)
                if coords != (None, None):
                    item["lat"], item["lon"] = coords
        item["country"] = country
        if slug:
            item["website"] = f"https://{domain}/store-locations/{slug}"

        if hours_text and isinstance(hours_text, str):
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string(hours_text)
                item["opening_hours"] = oh
            except Exception:
                pass

        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
