from locations.categories import Categories
from locations.storefinders.uberall import UberallSpider


# Does have Linked Data, but requires JS to load it
class AldiNordDKSpider(UberallSpider):
    name = "aldi_nord_dk"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373", "extras": Categories.SHOP_SUPERMARKET.value}
    key = "ALDINORDDK_X4Jlb165jBUstmddaEYk5GcxWffPqd"
