from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class AveraUSSpider(YextAnswersSpider):
    name = "avera_us"
    item_attributes = {"operator": "Avera Health", "operator_wikidata": "Q4828238"}
    experience_key = "locator"
    api_key = "413a34db5016c35c9f4a790833a03dd3"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        # Avera Health operates many different types of facility (hospitals,
        # clinics, pharmacies, fitness centres, hospices, nursing homes,
        # etc.) under a single operator, so a category tag has to be worked
        # out per location rather than applied uniformly for the whole
        # spider. Only the location's own name is used as a signal here —
        # Yext's c_specialtyLine2 field lists services *offered* at a
        # location (e.g. a hospital that also offers rehab, or a clinic with
        # an on-site lab draw), not what the location fundamentally is, and
        # using it misclassified real hospitals/clinics as rehab/lab.
        name = (item.get("name") or "").lower()

        def has(*keywords: str) -> bool:
            return any(keyword in name for keyword in keywords)

        if has("pharmacy"):
            apply_category(Categories.PHARMACY, item)
        elif has("hospice"):
            apply_category(Categories.HOSPICE, item)
        elif has("home medical equipment"):
            apply_category(Categories.SHOP_MEDICAL_SUPPLY, item)
        elif has("dialysis"):
            apply_category(Categories.DIALYSIS, item)
        elif has("urgent care"):
            apply_category(Categories.CLINIC_URGENT, item)
        elif has("blood bank", "blood donation"):
            apply_category(Categories.BLOOD_DONATION, item)
        elif has("laboratory"):
            apply_category(Categories.MEDICAL_LABORATORY, item)
        elif has("imaging", "radiology"):
            apply_category(Categories.MEDICAL_IMAGING, item)
        elif has("assisted living", "retirement community", "independent living"):
            apply_category(Categories.ASSISTED_LIVING, item)
        elif has("skilled nursing", "nursing facility", "nursing home"):
            apply_category(Categories.NURSING_HOME, item)
        elif has("rehabilitation", "rehab", "avera therapy") and not has("sports medicine"):
            apply_category(Categories.REHABILITATION, item)
        elif has("avera sports", "fitness center", "fitness centre", "human performance"):
            apply_category(Categories.GYM, item)
        elif has("hospital"):
            apply_category(Categories.HOSPITAL, item)
        else:
            apply_category(Categories.CLINIC, item)

        yield item
