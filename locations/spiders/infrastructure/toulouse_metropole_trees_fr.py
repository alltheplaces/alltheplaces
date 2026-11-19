from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class ToulouseMetropoleTreesFRSpider(OpendatasoftExploreSpider):
    name = "toulouse_metropole_trees_fr"
    item_attributes = {"nsi_id": "N/A"}
    dataset_attributes = (
        OpendatasoftExploreSpider.dataset_attributes
        | Licenses.ETALAB2.value
        | {"attribution:name": "Toulouse Métropole"}
    )
    api_endpoint = "https://data.toulouse-metropole.fr/api/explore/v2.1/"
    dataset_id = "arbres-urbains"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Stumps and dead standing trunks
        if feature["genre"] in ("Souche", "Chandelle"):
            return
        item["city"] = feature["commune"]
        apply_category(Categories.NATURAL_TREE, item)
        if feature["genre"] and not feature["genre"].startswith("0_"):
            item["extras"]["genus"] = feature["genre"]
            if feature["espece"] and feature["espece"] != "sp." and not feature["espece"].startswith("0_"):
                item["extras"]["species"] = f"{feature['genre']} {feature['espece'].replace('x.', 'x ')}"
        item["extras"]["start_date"] = feature["date_plantation"]
        yield item
