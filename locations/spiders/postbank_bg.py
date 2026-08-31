from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Fetched from within the locator page so that the request carries the
# browser's own origin, cookies and headers.
LOCATIONS_FETCH_JS = """async () => {
    const response = await fetch("/en/api/locations/locations", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
        body: "contextItemPath=" + encodeURIComponent("/sitecore/content/postbank/home"),
    });
    if (!response.ok) throw new Error("locations API returned HTTP " + response.status);
    return await response.json();
}"""


class PostbankBGSpider(JSONBlobSpider, CamoufoxSpider):
    name = "postbank_bg"
    item_attributes = {"brand": "Пощенска банка", "brand_wikidata": "Q7234083", "country": "BG"}
    allowed_domains = ["content.postbank.bg"]
    no_refs = True
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "fetch"]
    }

    async def start(self) -> AsyncIterator[Request]:
        # Akamai rejects a bare request to the API, so load the locator page in
        # the browser first and call the API from that page.
        yield Request(
            "https://content.postbank.bg/Contacts/Network",
            meta={"camoufox_page_methods": [PageMethod("evaluate", LOCATIONS_FETCH_JS)]},
            callback=self.parse,
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        return [
            dict(branch, city=city["city"])
            for city in response.meta["camoufox_page_methods"][0].result
            for branch in city["branches"]
        ]

    def pre_process_data(self, feature: dict) -> None:
        feature["coords"] = feature.pop("branchCoords")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        closed_markers = " ".join(filter(None, [feature["worktime"], feature["workhours"], feature["address"]])).lower()
        if "временно" in closed_markers or "temporar" in closed_markers:
            return

        item["opening_hours"] = OpeningHours()
        if feature["worktime"] is not None:
            item["opening_hours"].add_ranges_from_string(feature["worktime"].replace(";", ":").replace("<br/>", "; "))

        if feature["isATM"]:
            apply_category(Categories.ATM, item)
            apply_yes_no(Extras.CASH_IN, item, feature["isATMWithDeposit"])
        elif feature["isBranch"]:
            apply_category(Categories.BANK, item)
            apply_yes_no("self_service", item, feature["isSelfServiceZone"])
        yield item
