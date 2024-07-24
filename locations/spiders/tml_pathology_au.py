from locations.categories import Categories
from locations.spiders.dorevitch_pathology_au import DorevitchPathologyAUSpider


class TmlPathologyAUSpider(DorevitchPathologyAUSpider):
    name = "tml_pathology_au"
    item_attributes = {
        "brand": "TML Pathology",
        "brand_wikidata": "Q126165745",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    company_code = "tml"
