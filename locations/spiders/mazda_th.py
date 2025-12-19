from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_TH, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaTHSpider(JSONBlobSpider):
    name = "mazda_th"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["www.mazda.co.th"]
    start_urls = ["https://www.mazda.co.th/th/dealer"]
    locations_key = ["pageProps", "getDataDealerAll"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url=self.start_urls[0], callback=self.parse_next_build_id)

    def parse_next_build_id(self, response: Response) -> Iterable[Request]:
        next_build_manifest_url = (
            response.xpath('//script[contains(@src, "/_buildManifest.js")]/@src')
            .get()
            .removeprefix("/_next/static/")
            .removesuffix("/_buildManifest.js")
        )
        yield Request(url=f"https://www.mazda.co.th/_next/data/{next_build_manifest_url}/th/dealer.json")

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("detail"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)

        if feature["ServiceTypeID"] and len(feature["ServiceTypeID"]) > 0:
            service_item = item.deepcopy()
            service_item["ref"] = service_item["ref"] + "_Service"
            service_item["phone"] = feature.get("TelephoneService")
            service_item["opening_hours"] = OpeningHours()
            hours_text = (
                feature["ServicesBusinessHours"]
                .removeprefix("เปิด ")
                .replace("เปิดทุกวัน", "วันจันทร์-วันอาทิตย์")
                .replace(",", "")
            )
            if hours_text.startswith("0"):
                hours_text = "วันจันทร์-วันอาทิตย์: " + hours_text
            service_item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_TH)
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        item["ref"] = item["ref"] + "_Sales"
        item["phone"] = feature.get("TelephoneSales")
        item["opening_hours"] = OpeningHours()
        hours_text = (
            feature["SalesBusinessHours"].removeprefix("เปิด ").replace("เปิดทุกวัน", "วันจันทร์-วันอาทิตย์").replace(",", "")
        )
        if hours_text.startswith("0"):
            hours_text = "วันจันทร์-วันอาทิตย์: " + hours_text
        item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_TH)
        apply_category(Categories.SHOP_CAR, item)
        yield item
