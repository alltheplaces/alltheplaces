from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.zabka_pl import ZabkaPLSpider

# Polish day abbreviation keys in the opening_hours API field → ISO day abbreviations
PL_DAYS = {
    "PON": "Mo",
    "WT": "Tu",
    "SR": "We",
    "CZW": "Th",
    "PT": "Fr",
    "SOB": "Sa",
    "NIEDZ": "Su",
}

PARTNERS = {
    "zabka": (ZabkaPLSpider.item_attributes, Categories.SHOP_CONVENIENCE),
    "abc": ({"brand_wikidata": "Q11683985"}, Categories.SHOP_CONVENIENCE),
    "inmedio": ({"brand_wikidata": "Q108599411"}, Categories.SHOP_NEWSAGENT),
    "lewiatan": ({"brand": "Lewiatan", "brand_wikidata": "Q11755396"}, Categories.GENERIC_SHOP),
    "shell": ({"brand_wikidata": "Q124359752"}, Categories.SHOP_CONVENIENCE),
    "kaufland": ({"brand_wikidata": "Q685967"}, Categories.SHOP_SUPERMARKET),
    "eurosklep": ({"brand": "Euro Sklep", "brand_wikidata": "Q11702591"}, Categories.GENERIC_SHOP),
    "groszek": ({"brand": "Groszek", "brand_wikidata": "Q9280965"}, Categories.GENERIC_SHOP),
    "relay": ({"brand_wikidata": "Q3424298"}, Categories.SHOP_NEWSAGENT),
    "1minute": ({"name": "1 Minute"}, Categories.SHOP_NEWSAGENT),
    "apimarket": ({"name": "API Market"}, Categories.SHOP_SUPERMARKET),
    "kolporter": ({"name": "Kolporter"}, Categories.SHOP_NEWSAGENT),
    "lidl": ({"brand": "Lidl", "brand_wikidata": "Q151954"}, Categories.SHOP_SUPERMARKET),
    "moya": ({}, Categories.GENERIC_POI),
    "point": ({}, Categories.GENERIC_POI),
}


class DhlPLSpider(Spider):
    """DHL parcel pick-up points and parcel lockers (DHL BOX 24/7) in Poland.

    Data comes from two endpoints on parcelshop.dhl.pl:
      - /mapa/points  returns all ~24 000 location IDs, lat/lon, and type
      - /mapa/point?id=<ID>  returns full address, name, and opening hours
    """

    name = "dhl_pl"
    allowed_domains = ["parcelshop.dhl.pl"]
    start_urls = ["https://parcelshop.dhl.pl/mapa/points"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for point in response.json():
            item = Feature()
            item["ref"] = point["ID"]
            item["lat"] = point["SZ_GEOGRAFICZNA"]
            item["lon"] = point["DL_GEOGRAFICZNA"]
            if point["P_TYPE"] == "ecobox":
                item["brand_wikidata"] = "Q115568785"
                apply_category(Categories.PARCEL_LOCKER, item)
                yield item
                continue
                yield Request(
                    "https://parcelshop.dhl.pl/mapa/point?id={id}".format(id=point["ID"]),
                    callback=self.parse_detail,
                    cb_kwargs={"point_type": point.get("P_TYPE", ""), "item": item},
                )
            elif brand_cat := PARTNERS.get(point["P_TYPE"]):
                item["extras"]["post_office"] = "post_partner"
                item.update(brand_cat[0])
                apply_category(brand_cat[1], item)
                yield item
            else:
                item["extras"]["post_office"] = "post_partner"
                apply_category(Categories.GENERIC_POI, item)
                self.logger.error("Unexpected type: {}".format(point["P_TYPE"]))
                yield item

    def parse_detail(self, response: Response, point_type: str, item: Feature, **kwargs: Any) -> Any:
        payload = response.json()
        if payload.get("status") != "ok":
            return
        data = payload["data"]

        item["name"] = data.get("name")
        item["street"] = data.get("street")
        item["housenumber"] = data.get("houseNo")
        item["postcode"] = data.get("zip")
        item["city"] = data.get("city")

        # Parse structured opening hours
        oh_data = data.get("opening_hours") or {}
        if oh_data:
            oh = OpeningHours()
            for pl_day, iso_day in PL_DAYS.items():
                open_time = oh_data.get(f"{pl_day}_open")
                close_time = oh_data.get(f"{pl_day}_close")
                if open_time and close_time:
                    oh.add_range(iso_day, open_time, close_time)
            item["opening_hours"] = oh

        yield item
