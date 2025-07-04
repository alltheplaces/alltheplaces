import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FoussierFRSpider(Spider):
    name = "foussier_fr"
    item_attributes = {"brand": "Foussier", "brand_wikidata": "Q135189843"}
    start_urls = ["https://www.foussier.fr/magasins-foussier-en-france"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in DictParser.get_nested_key(
            json.loads(response.xpath('//script[@type="application/json"][@id="__NEXT_DATA__"]/text()').get()), "stores"
        )["entries"]:
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["libelle"].removeprefix("Foussier ")
            item["street_address"] = merge_address_lines(
                [location["adresse"]["adresse1"], location["adresse"]["adresse2"]]
            )
            item["postcode"] = location["adresse"]["codePostal"]
            item["city"] = location["adresse"]["ville"]
            item["phone"] = location["adresse"].get("telephoneFixe") or location["adresse"].get("telephoneMobile")
            item["lat"] = location["adresse"]["latitude"]
            item["lon"] = location["adresse"]["longitude"]

            apply_category(Categories.SHOP_HARDWARE, item)

            yield item
