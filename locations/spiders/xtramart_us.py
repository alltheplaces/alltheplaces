from locations.storefinders.uberall import UberallSpider


class XtramartUSSpider(UberallSpider):
    name = "xtramart_us"
    item_attributes = {"brand": "XtraMart", "brand_wikidata": "Q119586946"}
    key = "2x16cWCMQlofTBOi3CnPe0a1vd15b1"
