import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class SparGBSpider(scrapy.Spider):
    name = "spar_gb"
    item_attributes = {"brand": "SPAR", "brand_wikidata": "Q610492"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.spar.co.uk/umbraco/api/storelocationapi/stores?pageNumber=1"]

    def parse(self, response, **kwargs):
        stores = response.json().get("storeList", [])
        if len(stores) == 10:
            page_no = response.meta.get("page", 1) + 1
            yield JsonRequest(
                url=f"https://www.spar.co.uk/umbraco/api/storelocationapi/stores?pageNumber={page_no}",
                meta={"page": page_no},
            )

        for store in stores:
            item = DictParser.parse(store)
            item["website"] = "https://www.spar.co.uk" + store["StoreUrl"]
            item["street_address"] = clean_address(
                [store.get("Address1"), store.get("Address2"), store.get("Address3")]
            )

            services = [s["Name"] for s in store["Services"]]

            apply_yes_no(Extras.ATM, item, "ATM" in services)
            apply_yes_no("sells:costa", item, "Costa" in services)
            apply_yes_no("sells:starbucks", item, "Starbucks" in services)
            apply_yes_no("sells:subway", item, "SubWay" in services)
            apply_yes_no("sells:alcohol", item, "Off Licence" in services)
            apply_yes_no("sells:lottery", item, "Lottery" in services)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in services)
            apply_yes_no("cash_withdrawal", item, "Cash Back" in services)
            apply_yes_no("paypoint", item, "Paypoint" in services)
            apply_yes_no("payzone", item, "Payzone" in services)
            apply_yes_no(Extras.WIFI, item, "Wi-Fi" in services)

            apply_yes_no(PaymentMethods.APPLE_PAY, item, "Apple Pay" in services)
            apply_yes_no(PaymentMethods.CONTACTLESS, item, "Contactless" in services)

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
