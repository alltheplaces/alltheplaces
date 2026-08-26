from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response, TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class SigmaITSpider(JSONBlobSpider, CamoufoxSpider):
    name = "sigma_it"
    item_attributes = {"brand": "Sigma", "brand_wikidata": "Q3977979"}
    allowed_domains = ["www.supersigma.com"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "fetch"],
        "CAMOUFOX_MAX_CONTEXTS": 1,
        "CAMOUFOX_MAX_PAGES_PER_CONTEXT": 1,
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.supersigma.com/punti-vendita/",
            meta={
                "camoufox_page_methods": [
                    PageMethod(
                        "evaluate",
                        """async () => {
                            const response = await fetch("/wp-admin/admin-ajax.php", {
                                method: "POST",
                                body: new URLSearchParams({
                                    action: "gmw_form_ajax_submission",
                                    submitted: "true",
                                    form_id: "2",
                                    form_values: "address%5B%5D=Napoli&distance=100000&units=metric&post%5B%5D=store&page=1&per_page=10000&lat=40.85177&lng=14.26812&swlatlng=&nelatlng=&form=2&action=fs",
                                }),
                            });
                            if (!response.ok) throw new Error("store search returned HTTP " + response.status);
                            return await response.json();
                        }""",
                    )
                ]
            },
            callback=self.parse,
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        return response.meta["camoufox_page_methods"][0].result["map_args"]["locations"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["ref"] = feature["location_id"]
        branch_name = feature["location_name"]
        if " di " in branch_name:
            branch_name = branch_name.split(" di ", 1)[1]
        elif " DI" in branch_name:
            branch_name = branch_name.split(" DI ", 1)[1]
        if " (" in branch_name:
            branch_name = branch_name.split(" (", 1)[0]
        item["branch"] = branch_name
        item.pop("name", None)
        item["street_address"] = item.pop("street")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield Request(
            url="https://www.supersigma.com/?p=" + feature["object_id"],
            meta={"item": item},
            callback=self.parse_store_page,
        )

    def parse_store_page(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["website"] = response.url  # The store's own slug, after the ?p= redirect
        item["phone"] = response.xpath('//div[img[contains(@src, "icon-phone.svg")]]/span/i/text()').get()
        item["email"] = response.xpath('//div[img[contains(@src, "icon-email.svg")]]/span/i/text()').get()
        item["opening_hours"] = OpeningHours()
        for day_row in response.xpath('//p[contains(@class, "timetable-row")]'):
            day = day_row.xpath('./span[contains(@class, "timetable-day")]/text()').get()
            times = day_row.xpath('./span[contains(@class, "timetable-hour")]/text()').get()
            item["opening_hours"].add_ranges_from_string(f"{day}: {times}", days=DAYS_IT, closed=CLOSED_IT)
        yield item
