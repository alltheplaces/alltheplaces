from time import struct_time
from urllib.parse import quote

from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

COUNTRY_TO_LANGUAGE = {
    "AE": "en",
    "AR": "es",
    "BE": "fr",
    "BR": "pt",
    "CH": "en",
    "CO": "es",
    "ES": "es",
    "FR": "fr",
    "GB": "en",
    "GR": "en",
    "JP": "ja",
    "LU": "en",
    "MA": "en",
    "MX": "es",
    "NL": "nl",
    "TR": "tr",
    "UK": "en",
    "US": "en",
    "UY": "en",
}

DELIVERY_PARTNERS = {
    "pedidosYa": "Pedidos Ya",
    "clickAndConnect": None,
    "uberEats": "Ubereats",
    "deliveroo": "Deliveroo",
    "justEat": "Just Eat",
    "rappi": "Rappi",
}


def time_dict_to_struct(t):
    if t is None:
        return None
    if t["hours"] >= 24:
        t["hours"] = 23
        t["minutes"] = 59
    return struct_time((1900, 1, 1, t["hours"], t.get("minutes", 0), 0, 0, 1, -1))


class LePainQuotidienSpider(Spider):
    name = "le_pain_quotidien"
    item_attributes = {"brand": "Le Pain Quotidien", "brand_wikidata": "Q2046903"}

    def start_requests(self):
        yield Request(
            "https://api.obenan.com/api/v1/listing/search",
            headers={
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbkFwaURhdGEiOnsiaWQiOiIxNzUifSwiaWF0IjoxNjgzNzMwNzAyfQ.Oy4pCx-1kTiRVifVdXDS6B5ymu0wC4E4Ieq5HewoBfY"
            },
        )

    def parse(self, response):
        for location in response.json()["data"]["data"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["country"] = location["regionCode"]
            item["geometry"] = location["latlng"]
            item["street_address"] = merge_address_lines(location["addressLines"])
            # Note: Doesn't work for Mexico (slug missing)
            item["website"] = (
                f"https://www.lepainquotidien.com/{location['regionCode'].lower()}/{COUNTRY_TO_LANGUAGE[location['regionCode']]}/locations/{quote(location['slug'])}/{quote(location['addressLines'][0].replace(' ', '-'))}"
            )

            oh = OpeningHours()
            for period in location["regularHours"]["periods"]:
                oh.add_range(
                    period["openDay"],
                    time_dict_to_struct(period.get("openTime")),
                    time_dict_to_struct(period.get("closeTime")),
                )
            item["opening_hours"] = oh

            delivery_options = {partner for partner, url in location["deliveryOptions"].items() if url != ""}
            if len(delivery_options) > 0:
                apply_yes_no(Extras.DELIVERY, item, True)
                for partner in delivery_options:
                    if partner not in DELIVERY_PARTNERS:
                        self.crawler.stats.inc_value(f"atp/le_pain_quotidien/unmapped_delivery/{partner}")
                item["extras"]["delivery:partner"] = ";".join(
                    filter(None, (DELIVERY_PARTNERS.get(partner) for partner in delivery_options))
                )

            yield item
