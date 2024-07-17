from locations.categories import Categories
from locations.spiders.dorevitch_pathology_au import DorevitchPathologyAUSpider


class AbbottPathologyAUSpider(DorevitchPathologyAUSpider):
    name = "abbott_pathology_au"
    item_attributes = {
        "brand": "Abbott Pathology",
        "brand_wikidata": "Q126165721",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    company_code = "abbott"
