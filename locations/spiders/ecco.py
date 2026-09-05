from typing import Any, AsyncIterator

from scrapy import Request
from scrapy.http import TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# ecco.com sits behind a Vercel bot-management checkpoint, and the real
# store data now lives behind a commercetools Storefront API that requires a
# short-lived (~3 hour) bearer token minted per-session by the site's own
# NextAuth backend. Loading the storefront in a real browser clears the
# checkpoint and lets the site's own client-side JS establish an anonymous
# NextAuth session; the token is then read back from that same page's own
# /api/auth/session endpoint and used, from within the page (so the
# commercetools request carries the browser's own origin), to page through
# every store. This avoids ever hardcoding a token that will go stale.
STORES_FETCH_JS = """async () => {
    // The site's own client-side JS asynchronously signs in an anonymous
    // NextAuth session shortly after the page loads. Poll the session
    // endpoint (rather than racing a specific network event) until that
    // sign-in has completed and a commercetools access token is present.
    let token = null;
    for (let attempt = 0; attempt < 20 && !token; attempt++) {
        const session = await (await fetch("/api/auth/session")).json();
        token = session && session.accessToken;
        if (!token) await new Promise((resolve) => setTimeout(resolve, 500));
    }
    if (!token) throw new Error("no commercetools access token in ecco.com session after waiting");

    const where = encodeURIComponent(
        'custom(fields(store_CF_StoreLocator=true AND store_CF_Deleted=false AND store_CF_Ownership="ECCO"))'
    );
    const limit = 500;
    let offset = 0;
    let results = [];
    while (true) {
        const url = `https://api.europe-west1.gcp.commercetools.com/ecco-eap-prod/stores?offset=${offset}&limit=${limit}&expand=custom.fields.store_CF_OperatingHours&where=${where}`;
        const resp = await fetch(url, {headers: {authorization: "Bearer " + token}});
        if (!resp.ok) throw new Error("commercetools stores API returned HTTP " + resp.status);
        const data = await resp.json();
        results = results.concat(data.results);
        if (data.total <= offset + limit) break;
        offset += limit;
    }
    return results;
}"""


class EccoSpider(CamoufoxSpider):
    name = "ecco"
    item_attributes = {"brand": "Ecco", "brand_wikidata": "Q1280255"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "script", "xhr", "fetch"],
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            "https://us.ecco.com/",
            meta={"camoufox_page_methods": [PageMethod("evaluate", STORES_FETCH_JS)]},
            callback=self.parse,
        )

    def parse(self, response: TextResponse) -> Any:
        for result in response.meta["camoufox_page_methods"][0].result:
            if store := result.get("custom", {}).get("fields", {}):
                if store.get("store_CF_Street1") and store.get("store_CF_Latitude"):
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
                    apply_category(Categories.SHOP_SHOES, item)
                    if store_type := store.get("store_CF_StoreType"):
                        item.set_tag("store_type", store_type)

                    try:
                        if hours := store.get("store_CF_OperatingHours", {}).get("obj", {}).get("value"):
                            item["opening_hours"] = self.parse_opening_hours(hours)
                    except Exception as e:
                        self.logger.error(f"Failed to parse opening hours: {e}")

                    yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hours in rules.items():
            opening_hours.add_range(day, hours["open"], hours["close"], "%H:%M:%S")
        return opening_hours
