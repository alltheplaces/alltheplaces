from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class SanMateoCountyLibrariesUSSpider(BiblioCommonsSpider):
    name = "san_mateo_county_libraries_us"
    item_attributes = {"operator": "San Mateo County Libraries", "operator_wikidata": "Q21163258"}
    library_id = "smcl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "Bookmobile":
            # A mobile service whose address fields describe its varying stops.
            return
        if branch.startswith("Pacifica Sanchez Outpost"):
            # A self-service lending machine at the Pacifica Sanchez Library address.
            return

        item["branch"] = branch
        item["name"] = "{} Library".format(branch)
        apply_category(Categories.LIBRARY, item)

        yield item
