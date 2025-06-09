from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class RegisGBSpider(UberallSpider):
    name = "regis_gb"
    item_attributes = {"brand": "Regis Salons", "brand_wikidata": "Q110166032"}
    #    start_urls = ["https://locator.uberall.com/api/storefinders/616eo7rrGeXiZ0jL1wrJ2JAlyx5RxR/locations/all?v=20230110&language=en&fieldMask=id&fieldMask=identifier&fieldMask=googlePlaceId&fieldMask=lat&fieldMask=lng&fieldMask=name&fieldMask=country&fieldMask=city&fieldMask=province&fieldMask=streetAndNumber&fieldMask=zip&fieldMask=businessId&fieldMask=addressExtra&country=UK"]
    key = "616eo7rrGeXiZ0jL1wrJ2JAlyx5RxR"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Regis Salon ")
        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item
