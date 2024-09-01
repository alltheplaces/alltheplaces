from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class MuggAndBeanAfricaSpider(YextSearchSpider):
    name = "mugg_and_bean_africa"
    item_attributes = {"brand": "Mugg & Bean", "brand_wikidata": "Q6932113"}
    host = "https://location.muggandbean.africa"

    def parse_item(self, location, item):
        item["branch"] = location["profile"].get("geomodifier")
        item["extras"]["website:menu"] = location["profile"].get("menuUrl")
        if "c_muggAndBeanLocatorFilters" in location["profile"]:
            apply_yes_no(Extras.HALAL, item, "Halaal" in location["profile"]["c_muggAndBeanLocatorFilters"])
        if payment_methods := location["profile"].get("c_customPaymentMethods"):
            apply_yes_no(PaymentMethods.CASH, item, "Cash" in payment_methods, False)
            apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "Card" in payment_methods, False)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "Card" in payment_methods, False)
            apply_yes_no(PaymentMethods.MPESA, item, "Mpesa" in payment_methods, False)
        if item["website"] == "https://location.muggandbean.africa/kenya":
            item["website"] = location["profile"]["c_pagesURL"]
        yield item
