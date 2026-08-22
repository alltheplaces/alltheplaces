from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class EccoSpider(PlaywrightSpider):
    name = "ecco"
    item_attributes = {"brand": "Ecco", "brand_wikidata": "Q1280255"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def make_request(self, offset: int, limit: int = 500) -> JsonRequest:
        return JsonRequest(
            url=f'https://api.europe-west1.gcp.commercetools.com/ecco-eap-prod/stores?offset={offset}&limit={limit}&expand=custom.fields.store_CF_OperatingHours&where=custom(fields(store_CF_StoreLocator=true AND store_CF_Deleted=false AND store_CF_Ownership="ECCO"))',
            # TODO: Implement dynamic access-token generation via:
            # https://us.ecco.com/api/auth/session
            # This endpoint itself requires a valid session token, so implementing the
            # complete token-generation flow does not currently appear feasible.
            # For now, a token with an approximate one-month lifetime is hardcoded.
            headers={"authorization": "Bearer qubSH5SiQ3HTJM2p1Tu_-mpmDaKBgMtE"},
            cb_kwargs=dict(offset=offset, limit=limit),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, offset: int, limit: int) -> Any:
        for result in response.json()["results"]:
            if store := result.get("custom", {}).get("fields", {}):
                if store.get("store_CF_Street1") or store.get("store_CF_Latitude"):
                    item = Feature()
                    item["ref"] = result["id"]
                    item["name"] = store.get("store_CF_Name1", {}).get("en")
                    item["street_address"] = merge_address_lines(
                        [store.get("store_CF_Street1", {}).get("en"), store.get("store_CF_Street2", {}).get("en")]
                    )
                    item["city"] = store.get("store_CF_City", {}).get("en")
                    item["state"] = store.get("store_CF_Region")
                    item["postcode"] = store.get("store_CF_PostalCode")
                    item["phone"] = store.get("store_CF_Telephone")
                    item["country"] = store.get("store_CF_Country")
                    item["email"] = store.get("store_CF_Email")
                    item["lat"] = store.get("store_CF_Latitude")
                    item["lon"] = store.get("store_CF_Longitude")
                    item["extras"]["store_type"] = store.get("store_CF_StoreType")

                    try:
                        if hours := store.get("store_CF_OperatingHours", {}).get("obj", {}).get("value"):
                            item["opening_hours"] = self.parse_opening_hours(hours)
                    except Exception as e:
                        self.logger.error(f"Failed to parse opening hours: {e}")

                    yield item

        if response.json()["total"] > offset + limit:
            yield self.make_request(offset + limit)

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hours in rules.items():
            opening_hours.add_range(day, hours["open"], hours["close"], "%H:%M:%S")
        return opening_hours
