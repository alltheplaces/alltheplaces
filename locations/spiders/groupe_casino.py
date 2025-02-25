from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class GroupeCasinoSpider(Spider):
    name = "groupe_casino"
    brands = {
        "30835": ("Casino Bio", "", None),
        "30836": ("Casino Home", "", None),
        "30837": ("Casino PauseDéj", "", None),
        "30838": ("Casino Shop", "Q89029601", Categories.SHOP_CONVENIENCE),
        "30840": ("Casino Toutpres", "", None),
        "30842": ("Le Petit Casino", "Q89029249", Categories.SHOP_CONVENIENCE),
        "30843": ("Le Petit Casino", "Q89029249", Categories.SHOP_CONVENIENCE),  # Petit Casino
        "30844": ("Spar", "Q610492", Categories.SHOP_CONVENIENCE),
        "30845": ("Spar", "Q610492", Categories.SHOP_SUPERMARKET),
        "30846": ("Casino", "Q89029184", Categories.SHOP_SUPERMARKET),
        "30847": ("Vival", "Q7937525", Categories.SHOP_CONVENIENCE),
    }

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://spar.casino.fr/store-api/business/search?page={page}&per_page=100",
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("businesses", []):
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([item.pop("addr_full", ""), location.get("address2")])
            if contacts := location.get("contacts"):
                item["phone"] = "; ".join(contacts[0].get("phone_numbers"))
                item["email"] = contacts[0].get("email")

            location_name = location["name"].lower()
            if "casino" in location_name:
                item["website"] = f'https://petitcasino.casino.fr/fr/stores/{location["code"]}'
            elif "spar" in location_name:
                item["website"] = f'https://spar.casino.fr/fr/stores/{location["code"]}'
            elif "vival" in location_name:
                item["website"] = f'https://vival.casino.fr/fr/stores/{location["code"]}'

            if location.get("groups"):
                item["brand"], item["brand_wikidata"], category = self.brands.get(
                    str(location["groups"][0]), ("", "", None)
                )
                if category is not None:
                    apply_category(category, item)
            else:
                self.crawler.stats.inc_value(f'atp/{self.name}/unknown_brand/{location["name"]}')

            yield item

        if response.meta["page"] < response.json()["max_page"]:
            yield self.make_request(response.meta["page"] + 1)
