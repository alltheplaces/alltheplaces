from typing import AsyncIterator

from scrapy import Request, Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature


class GemeenteAmsterdamTreesNLSpider(Spider):
    name = "gemeente_amsterdam_trees_nl"
    item_attributes = {"operator": "Gemeente Amsterdam", "operator_wikidata": "Q9899", "nsi_id": "N/A"}
    allowed_domains = ["api.data.amsterdam.nl"]
    api_url = "https://api.data.amsterdam.nl/v1/bomen/v2/stamgegevens/?_format=json&_pageSize=1000&_sort=id&id[gt]={}"
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.api_url.format(0), headers={"Accept-Crs": "EPSG:4326"})

    def parse(self, response: TextResponse):
        trees = response.json()["_embedded"]["stamgegevens"]
        for tree in trees:
            # The register keeps the stumps of felled trees.
            if tree["typeObject"] == "Stobbe":
                continue
            item = Feature(ref=str(tree["id"]), geometry=tree["geometrie"])
            apply_category(Categories.NATURAL_TREE, item)
            if tree["soortnaam"] and tree["soortnaam"] != "Onbekend":
                item["extras"]["genus"] = tree["soortnaam"].split(" ")[0]
                if " " in tree["soortnaam"]:
                    item["extras"]["species"] = tree["soortnaam"]
            if tree["jaarVanAanleg"]:
                item["extras"]["start_date"] = str(tree["jaarVanAanleg"])
            yield item

        # The API refuses page numbers above 100, so page by id instead.
        if trees:
            yield Request(self.api_url.format(trees[-1]["id"]), headers={"Accept-Crs": "EPSG:4326"})
