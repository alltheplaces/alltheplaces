from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider

# Names as signed and shown on sjpl.org where they differ from "<branch> Branch Library".
NAMES = {
    "Alum Rock": "Dr. Roberto Cruz Alum Rock Branch Library",
    "East SJ Carnegie": "East San José Carnegie Branch Library",
    "King Library": "Dr. Martin Luther King, Jr. Library",
    "Mt. Pleasant": "Mt. Pleasant Neighborhood Library",
    "Tully": "Tully Community Branch Library",
}


class SanJosePublicLibraryUSSpider(BiblioCommonsSpider):
    name = "san_jose_public_library_us"
    item_attributes = {"operator": "San José Public Library", "operator_wikidata": "Q1084981"}
    library_id = "sjpl"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        item["name"] = NAMES.get(branch, "{} Branch Library".format(branch))
        if branch != "King Library":
            item["branch"] = branch
        apply_category(Categories.LIBRARY, item)
        yield item
