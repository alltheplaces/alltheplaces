from typing import Iterable

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.yext_search import YextSearchSpider


class NisalocalGBSpider(YextSearchSpider):
    name = "nisalocal_gb"
    item_attributes = {"brand": "Nisa", "brand_wikidata": "Q16999069"}
    host = "https://www.nisalocally.co.uk/stores"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        profile = location["profile"]
        item["ref"] = "https://www.nisalocally.co.uk/stores/#{}".format(item["ref"])
        item["website"] = profile.get("c_pagesURL")
        # Some coordinates are placeholders rounded to whole degrees, so take the first precise one
        for field in ("yextDisplayCoordinate", "geocodedCoordinate", "yextRoutableCoordinate", "displayCoordinate"):
            if (c := profile.get(field)) and not (float(c["lat"]).is_integer() or float(c["long"]).is_integer()):
                item["lat"], item["lon"] = c["lat"], c["long"]
                break

        if "Nisa Extra" in item["name"]:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        # Services are split over two fields, spelt with ("Pay Point") and without ("PayPoint") spaces
        services = {
            s.replace(" ", "") for s in (profile.get("c_pagesServices") or []) + (profile.get("services") or [])
        }
        apply_yes_no(Extras.ATM, item, any(s.startswith("CashMachine") for s in services))
        apply_yes_no(Extras.PARCEL_PICKUP, item, "ParcelCollection" in services)
        apply_yes_no(Extras.DELIVERY, item, "DeliveryServices" in services)
        apply_yes_no(Extras.CAR_WASH, item, any(s.startswith("CarWash") for s in services))
        apply_yes_no(Extras.LAUNDRY, item, "LaundryServices" in services)
        apply_yes_no(Extras.COPYING, item, "Photocopier" in services)
        apply_yes_no("sells:lottery", item, "NationalLottery" in services)
        apply_yes_no("paypoint", item, "PayPoint" in services)
        if "PostOffice" in services:
            item["extras"]["post_office"] = "post_partner"

        # The storefinder only reads the standard paymentOptions field
        payment_methods = {p.lower().replace(" ", "") for p in profile.get("c_pagesPaymentMethods") or []}
        apply_yes_no(PaymentMethods.CASH, item, "cash" in payment_methods)
        apply_yes_no(PaymentMethods.CARDS, item, "card" in payment_methods)
        apply_yes_no(PaymentMethods.CONTACTLESS, item, "contactless" in payment_methods)
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "applepay" in payment_methods)
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "googlepay" in payment_methods)

        yield item
