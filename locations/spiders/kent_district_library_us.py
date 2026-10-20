from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.biblio_commons import BiblioCommonsSpider


class KentDistrictLibraryUSSpider(BiblioCommonsSpider):
    name = "kent_district_library_us"
    item_attributes = {"operator": "Kent District Library", "operator_wikidata": "Q6391698"}
    library_id = "kdl"
    # Every location lists the same system-wide call centre number and inbox.
    drop_attributes = {"phone", "email"}

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch == "KDL Service and Meeting Center":
            # Administrative headquarters, "not open to the public for library services".
            return

        if branch == "Grattan Township Express Library":
            # A self-serve collection inside the township office, whose
            # hours it keeps.
            item["located_in"] = "Grattan Township Office"
            item["name"] = branch
        elif branch == "Amy Van Andel Library (Ada)":
            # The bracketed part is the town served, not part of the name.
            item["branch"], item["name"] = "Ada", "Amy Van Andel Library"
        else:
            # The Krause branch is rehoused while its building is rebuilt.
            branch = branch.removesuffix(" Temporary Location")
            if branch.endswith(" Branch"):
                item["branch"] = branch.removesuffix(" Branch")
                item["name"] = "{} Library".format(branch)
            else:
                item["name"] = branch

        apply_category(Categories.LIBRARY, item)

        yield item
