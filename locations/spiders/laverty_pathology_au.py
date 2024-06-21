from locations.categories import Categories
from locations.spiders.dorevitch_pathology_au import DorevitchPathologyAUSpider


class LavertyPathologyAUSpider(DorevitchPathologyAUSpider):
    name = "laverty_pathology_au"
    item_attributes = {
        "brand": "Laverty Pathology",
        "brand_wikidata": "Q105256033",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    company_code = "laverty"
