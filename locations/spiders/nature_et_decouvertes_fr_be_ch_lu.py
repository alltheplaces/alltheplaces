import json
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class NatureEtDecouvertesFRBECHLUSpider(Spider):
    name = "nature_et_decouvertes_fr_be_ch_lu"
    item_attributes = {"brand": "Nature & Découvertes", "brand_wikidata": "Q3337111"}
    start_urls = ["https://www.natureetdecouvertes.com/magasin/MagasinsJSonCallback"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.text.removeprefix("jsonCallback(").removesuffix(");"))
        for location in data.get("magasins"):
            item = Feature()
            item["ref"] = location.get("id")
            item["branch"] = location.get("nom").removeprefix(" Nature & Découvertes - ")
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lo")
            item["website"] = response.urljoin(location.get("nomUrl"))
            address_text = Selector(text=location.get("adresse"))  # .xpath("normalize-space()").get()
            item["street_address"] = address_text.xpath(".//p//text()").get()
            item["addr_full"] = merge_address_lines(
                [item["street_address"], address_text.xpath(".//p//text()[2]").get()]
            )
            apply_category(Categories.SHOP_OUTDOOR, item)

            yield item
