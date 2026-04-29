from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class LeCreusetSpider(UberallSpider):
    name = "le_creuset"
    item_attributes = {"brand": "Le Creuset","brand_wikidata": "Q555861",}
    # Name is always the brand name, not a branch name
    drop_attributes = {"name"}
    key = "VgqmJWo43GvGKKnJKwVn8SZjEXD4dW"
