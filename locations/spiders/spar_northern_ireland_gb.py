from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class SparNorthernIrelandGBSpider(Spider):
    name = "spar_northern_ireland_gb"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    EUROSPAR = {"brand": "Eurospar", "brand_wikidata": "Q12309283"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_requests(self, page: int) -> Request:
        return JsonRequest(
            f"https://www.spar-ni.co.uk/umbraco/api/storelocationapi/stores?pageNumber={page}", meta={"page": page}
        )

    def start_requests(self):
        yield self.make_requests(1)

    def parse(self, response, **kwargs):
        for location in response.json()["storeList"]:
            location["street_address"] = merge_address_lines(
                [location["Address1"], location["Address2"], location["Address3"]]
            )
            item = DictParser.parse(location)
            item["website"] = response.urljoin(location["StoreUrl"])

            if "EUROSPAR" in item["name"]:
                item.update(self.EUROSPAR)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item

        if len(response.json()["storeList"]) >= 10:
            yield self.make_requests(response.meta["page"] + 1)
