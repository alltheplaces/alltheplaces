from typing import Any

import reverse_geocoder
import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SkodaSpider(scrapy.Spider):
    name = "skoda"
    item_attributes = {"brand": "Škoda", "brand_wikidata": "Q29637"}
    start_urls = ["https://www.skoda-auto.com/company/importers"]

    available_countries = {
        107: ("de-DE", "DE"),
        109: ("en-mu", "MU"),
        202: ("nl-BE", "BE"),
        207: ("el-GR", "GR"),
        210: ("en-gb", "GB"),
        216: ("fr-LU", "LU"),
        218: ("nb-no", "NO"),
        222: ("sv-se", "SE"),
        223: ("de-ch", "CH"),
        233: ("hu-hu", "HU"),
        260: ("cs-CZ", "CZ"),
        261: ("pt-pt", "PT"),
        264: ("it-it", "IT"),
        282: ("es-ic", "ES"),
        285: ("zh-tw", "TW"),
        294: ("en-CY", "CY"),
        296: ("be-by", "BY"),
        298: ("sl-si", "SI"),
        308: ("fr-ma", "MA"),
        314: ("en-ba", "BA"),
        318: ("en-dz", "DZ"),
        334: ("fr-TN", "TN"),
        411: ("lv-LV", "LV"),
        423: ("tr-tr", "TR"),
        425: ("hr-hr", "HR"),
        428: ("en-sa", "SA"),
        438: ("nl-nl", "NL"),
        439: ("de-at", "AT"),
        441: ("fr-lu", "LU"),
        442: ("da-dk", "DK"),
        443: ("fi-fi", "FI"),
        447: ("el-gr", "GR"),
        451: ("bg-bg", "BG"),
        456: ("pl-pl", "PL"),
        457: ("sr-latn-CS", "RS"),
        462: ("et-ee", "EE"),
        472: ("lt-LT", "LT"),
        572: ("es-es", "ES"),
        599: ("ro-ro", "RO"),
        622: ("ro-MD", "MD"),
        654: ("sk-SK", "SK"),
        663: ("en-IN", "IN"),
        703: ("en-np", "NP"),
        710: ("en-kw", "KW"),
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

    def start_requests(self):
        # TODO: check how to get country ids dynamically
        for country_id, country in self.available_countries.items():
            yield JsonRequest(
                url="https://retailers.skoda-auto.com/api/{}/{}/Dealers/GetDealers".format(country_id, country[0]),
                meta={"country_code": country[1]},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("Items"):
            store.update(store.pop("Address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["ref"] = store["GlobalId"]
            item["state"] = store["District"]
            item["country"] = response.meta["country_code"]

            # Some of the coordinates have lat and lon switched and are usually bad.
            if result := reverse_geocoder.get((item["lat"], item["lon"]), mode=1, verbose=False):
                if item["country"] != result["cc"]:
                    item["lon"] = None
                    item["lat"] = None

            if store.get("HasSales"):
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no("service:vehicle:car_repair", item, store.get("HasServices"), True)
                apply_yes_no("second_hand", item, "UsedCarSales" in store["Sales"], True)
            elif store.get("HasServices"):
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
