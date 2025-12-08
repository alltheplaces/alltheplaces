from locations.storefinders.woosmap import WoosmapSpider


class MdITSpider(WoosmapSpider):
    name = "md_it"
    item_attributes = {
        "brand_wikidata": "Q3841263",
        "brand": "MD",
    }
    key = "woos-5a59cdb1-7aa1-3545-86dc-55b3527563b2"
    origin = "https://www.mdspa.it"
