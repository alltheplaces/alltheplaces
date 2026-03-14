from locations.categories import Categories
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class HyundaiFRSpider(UberallSpider):
    name = "hyundai_fr"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES | {"extras": Categories.SHOP_CAR.value}
    key = "gSNTstbODTSmkLJopDa5r6buAP1PHN"
