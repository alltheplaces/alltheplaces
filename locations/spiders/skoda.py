from copy import deepcopy
from typing import Any

import reverse_geocoder
import scrapy
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class SkodaSpider(scrapy.Spider):
    name = "skoda"
    item_attributes = {"brand": "Škoda", "brand_wikidata": "Q29637"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    available_countries_skoda_api = {
        107: ("de-DE", "DE"),
        109: ("en-mu", "MU"),
        202: ("nl-BE", "BE"),
        207: ("el-GR", "GR"),
        210: ("en-gb", "GB"),
        216: ("fr-LU", "LU"),
        217: ("en-mt", "MT"),
        218: ("nb-no", "NO"),
        222: ("sv-se", "SE"),
        223: ("de-ch", "CH"),
        260: ("cs-CZ", "CZ"),
        264: ("it-it", "IT"),
        282: ("es-ic", "ES"),
        285: ("zh-tw", "TW"),
        294: ("en-CY", "CY"),
        296: ("be-by", "BY"),
        308: ("fr-ma", "MA"),
        318: ("en-dz", "DZ"),
        334: ("fr-TN", "TN"),
        411: ("lv-LV", "LV"),
        423: ("tr-tr", "TR"),
        428: ("en-sa", "SA"),
        438: ("nl-nl", "NL"),
        442: ("da-dk", "DK"),
        443: ("fi-fi", "FI"),
        451: ("bg-bg", "BG"),
        456: ("pl-pl", "PL"),
        457: ("sr-latn-CS", "RS"),
        462: ("et-ee", "EE"),
        472: ("lt-LT", "LT"),
        572: ("es-es", "ES"),
        622: ("ro-MD", "MD"),
        654: ("sk-SK", "SK"),
        663: ("en-IN", "IN"),
        703: ("en-np", "NP"),
        710: ("en-kw", "KW"),
        715: ("en-BH", "BH"),
        745: ("en-ae", "AE"),
        777: ("en-bn", "BN"),
        824: ("en-nz", "NZ"),
        885: ("en-qa", "QA"),
        886: ("uk-UA", "UA"),
        941: ("en-IE", "IE"),
        959: ("en-AU", "AU"),
        961: ("ru-kz", "KZ"),
        995: ("fr-FR", "FR"),
    }

    available_countries_porsche_api = ["AL", "AT", "BA", "CL", "CO", "HR", "HU", "MK", "PT", "RO", "SG", "SI"]

    def start_requests(self):
        # TODO: check how to get country ids dynamically
        for country_id, country in self.available_countries_skoda_api.items():
            yield JsonRequest(
                url="https://retailers.skoda-auto.com/api/{}/{}/Dealers/GetDealers".format(country_id, country[0]),
                meta={"country_code": country[1]},
                callback=self.parse_skoda_api,
            )

        for country in self.available_countries_porsche_api:
            yield Request(
                url=f"https://groupcms-services-api.porsche-holding.com/v3/dealers/{country}/C",
                callback=self.parse_porsche_api,
            )

    def parse_skoda_api(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("Items"):
            store.update(store.pop("Address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["ref"] = store["GlobalId"]
            item["state"] = store["District"]
            item["country"] = response.meta["country_code"]
            # Some coordinates in TR have lat and lon switched and are usually bad.
            # Locations in ME have country property equal to RS
            if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                if item["country"] != result["cc"] and item["country"] == "TR":
                    item["lon"] = None
                    item["lat"] = None
                elif item["country"] != result["cc"] and item["country"] == "RS":
                    item["country"] = result["cc"]
            if store.get("HasSales"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR)
            if store.get("HasServices"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR_REPAIR)

    def parse_porsche_api(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("data"):
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["ref"] = store["bnr"]
            item["state"] = store.get("federalState")
            offers = store.get("contracts", {})
            if offers.get("sales"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR)
            if offers.get("service"):
                yield self.build_categorized_item(item, Categories.SHOP_CAR_REPAIR)

    def build_categorized_item(self, item: Feature, category: Categories) -> Feature:
        c_item = deepcopy(item)
        c_item["ref"] = f"{item['ref']}-{category}"
        apply_category(category, c_item)
        return c_item
