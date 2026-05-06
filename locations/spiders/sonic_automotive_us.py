from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.audi import AudiSpider
from locations.spiders.bmw_group import BmwGroupSpider
from locations.spiders.cadillac_us import CadillacUSSpider
from locations.spiders.chevrolet_pr_us import ChevroletPRUSSpider
from locations.spiders.ford import FordSpider
from locations.spiders.honda import HondaSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES
from locations.spiders.mercedes_benz_group import MercedesBenzGroupSpider
from locations.spiders.nissan import NissanSpider
from locations.spiders.porsche import PorscheSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES
from locations.spiders.toyota_eu import LEXUS_SHARED_ATTRIBUTES
from locations.spiders.volkswagen import VOLKSWAGEN_SHARED_ATTRIBUTES
from locations.spiders.volvo import VolvoSpider

BRANDS = {
    "audi": AudiSpider.item_attributes,
    "bmw": BmwGroupSpider.BRAND_MAPPING["BMW"],
    "cadillac": CadillacUSSpider.item_attributes,
    "chevrolet": ChevroletPRUSSpider.item_attributes,
    "chrysler": {"brand": "Chrysler", "brand_wikidata": "Q29610"},
    "dodge": {"brand": "Dodge", "brand_wikidata": "Q27564"},
    "ford": FordSpider.brand_mapping["Ford"],
    "gmc": {"brand": "GMC", "brand_wikidata": "Q28993"},
    "honda": HondaSpider.item_attributes,
    "hyundai": HYUNDAI_SHARED_ATTRIBUTES,
    "jaguar": {"brand": "Jaguar", "brand_wikidata": "Q21170490"},
    "land-rover": {"brand": "Land Rover", "brand_wikidata": "Q26777551"},
    "lexus": LEXUS_SHARED_ATTRIBUTES,
    "mercedes-benz": MercedesBenzGroupSpider.MERCEDES_BENZ,
    "mini": BmwGroupSpider.BRAND_MAPPING["MINI"],
    "nissan": NissanSpider.BRANDS["nissan"],
    "porsche": PorscheSpider.item_attributes,
    "subaru": {"brand": "Subaru", "brand_wikidata": "Q172741"},
    "toyota": TOYOTA_SHARED_ATTRIBUTES,
    "volkswagen": VOLKSWAGEN_SHARED_ATTRIBUTES,
    "volvo": VolvoSpider.item_attributes,
}


class SonicAutomotiveUSSpider(Spider):
    name = "sonic_automotive_us"
    item_attributes = {"operator": "Sonic Automotive", "operator_wikidata": "Q7561788"}
    start_urls = ["https://www.sonicautomotive.com/locations/index.htm"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//ol[@id="proximity-dealer-list"]/li'):
            item = Feature()
            item["ref"] = location.xpath("./@data-account-id").get()
            item["name"] = location.xpath('.//span[@class="org"]/text()').get()
            item["website"] = location.xpath(".//a/@href").get()
            item["lat"] = location.xpath('.//span[@class="latitude"]/text()').get()
            item["lon"] = location.xpath('.//span[@class="longitude"]/text()').get()
            item["street_address"] = location.xpath('.//span[@class="street-address"]/text()').get()
            item["city"] = location.xpath('.//span[@class="locality"]/text()').get()
            item["state"] = location.xpath('.//span[@class="region"]/text()').get()
            item["postcode"] = location.xpath('.//span[@class="postal-code"]/text()').get()
            item["phone"] = location.xpath('.//span[@data-phone-ref="SALES"]/text()').get()

            classes = location.xpath("./@class").get().split()
            for b, brand in BRANDS.items():
                if b in classes:
                    item.update(brand)
                    break
            else:
                if "collision" in classes:
                    continue
            apply_yes_no("second_hand", item, "preowned" in classes)

            apply_category(Categories.SHOP_CAR, item)

            yield item
