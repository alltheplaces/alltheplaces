from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser

CZECH_POST = {
    "brand": "Česká Pošta",
    "brand_wikidata": "Q341090",
    "operator": "Česká pošta, s.p.",
    "operator_wikidata": "Q341090",
}


class CzechPostCZSpider(Spider):
    name = "czech_post_cz"
    start_urls = ["https://www.postaonline.cz/en/vyhledat-pobocku"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://www.postaonline.cz/en/vyhledat-pobocku?p_p_id=findpostoffice_WAR_findpostportlet&p_p_lifecycle=2&p_p_resource_id=preparePostForMap",
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)

            item["website"] = item["extras"]["website:cs"] = (
                "https://www.postaonline.cz/detail-pobocky/-/pobocky/detail/{}".format(item["postcode"])
            )
            item["extras"]["website:en"] = "https://www.postaonline.cz/en/detail-pobocky/-/pobocky/detail/{}".format(
                item["postcode"]
            )

            if location["type"] == "Balíkovna":
                apply_category(Categories.GENERIC_POI, item)
                apply_yes_no("post_office=post_partner", item, True)
                apply_yes_no(Extras.PARCEL_PICKUP, item, True)
            elif location["type"] == "Depot":
                item.update(CZECH_POST)
                apply_category(Categories.POST_DEPOT, item)
            elif location["type"] == "Post office":
                item.update(CZECH_POST)
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] == "Postal agency":  # 6 "vydejniMisto"
                apply_category(Categories.GENERIC_POI, item)
                apply_yes_no("post_office=post_partner", item, True)
            elif location["type"] == "Service point":  # 43 "vydejniMisto"
                apply_category(Categories.GENERIC_POI, item)
                apply_yes_no("post_office=post_partner", item, True)
            elif location["type"] == "Technical outlet":  # 252 "technickaProvozovna"
                apply_category(Categories.GENERIC_POI, item)
                apply_yes_no("post_office=post_partner", item, True)
            elif location["type"] == "post.type.external.partner-box":  # "balikovna_box"
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                self.logger.error("Unexpected type: {}".format(location["type"]))

            yield item
