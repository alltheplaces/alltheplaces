from locations.categories import Categories
from locations.spiders.dorevitch_pathology_au import DorevitchPathologyAUSpider


class QMLPathologyAUSpider(DorevitchPathologyAUSpider):
    name = "qml_pathology_au"
    item_attributes = {
        "brand": "QML Pathology",
        "brand_wikidata": "Q126165557",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    company_code = "qml"
