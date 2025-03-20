from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiPRSpider(scrapy.Spider):
    name = "mitsubishi_pr"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishimotors.pr/concesionarios"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = list(
            chompjs.parse_js_objects(response.xpath('//*[contains(text(),"__PRELOADED_STATE__")]/text()').get())
        )
        for key in raw_data[1]["ROOT_QUERY"][
            'searchDealer({"criteria":{"filters":null,"language":"es","latitude":18.222271,"longitude":-66.430417,"market":"pr","radius":2000,"service":"all"},"path":"/pr/es/concesionarios"})'
        ]:
            address_data = raw_data[1][f'${key["id"]}.address']
            item = DictParser.parse(address_data)
            item["ref"] = key["id"]
            item["postcode"] = address_data["postalArea"]
            item["addr_full"] = merge_address_lines(
                [address_data["addressLine1"], address_data["addressLine2"], address_data["addressLine3"]]
            )
            item["phone"] = raw_data[1][f'${key["id"]}.phone']["phoneNumber"]
            item["branch"] = raw_data[1][key["id"]]["name"]
            apply_category(Categories.SHOP_CAR, item)
            yield item
