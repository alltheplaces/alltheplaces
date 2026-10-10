from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class MidContinentPublicLibraryUSSpider(BiblioCommonsSpider):
    name = "mid_continent_public_library_us"
    item_attributes = {"operator": "Mid-Continent Public Library", "operator_wikidata": "Q6840687"}
    library_id = "mymcpl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        # HEADQTRS is a processing facility with no public service; HILLCREST
        # and MARLBOROUG are Kansas City Parks community centres with public
        # computers, not library branches.
        if location["id"] in {"HEADQTRS", "HILLCREST", "MARLBOROUG"}:
            return

        if location["id"] != "GENEALOGY":
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["operator"]
        apply_category(Categories.LIBRARY, item)

        yield item
