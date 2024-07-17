from locations.categories import Categories
from locations.spiders.dorevitch_pathology_au import DorevitchPathologyAUSpider


class WesternDiagnosticPathologyAUSpider(DorevitchPathologyAUSpider):
    name = "western_diagnostic_pathology_au"
    item_attributes = {
        "brand": "Western Diagnostic Pathology",
        "brand_wikidata": "Q126165699",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    company_code = "wdp"
