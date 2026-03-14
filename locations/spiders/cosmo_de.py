from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class CosmoDESpider(KlierHairGroupSpider):
    name = "cosmo_de"
    start_urls = ["https://cosmohairshop.de/shops/"]
    item_attributes = {"brand": "Cosmo", "brand_wikidata": "Q116214796"}
    category = Categories.SHOP_HAIRDRESSER_SUPPLY

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("Cosmo Friseurzubehör und Friseurdienstleistungen "):
            item["branch"] = item.pop("name").removeprefix("Cosmo Friseurzubehör und Friseurdienstleistungen ")
            # apply_category(Categories.SHOP_HAIRDRESSER, item)
        elif item["name"].startswith("Cosmo Friseurzubehör "):
            item["branch"] = item.pop("name").removeprefix("Cosmo Friseurzubehör ")
            # apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        yield item
