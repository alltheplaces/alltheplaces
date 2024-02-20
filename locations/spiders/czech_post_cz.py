from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CzechPostCZSpider(Spider):
    name = "czech_post_cz"
    item_attributes = {"brand": "Česká pošta", "brand_wikidata": "Q341090"}
    start_urls = ["https://www.postaonline.cz/en/vyhledat-pobocku"]

    types = {
        "Balíkovna": {"amenity": "post_office", "post_office": "post_partner", "parcel_pickup": "yes"},
        "Depot": Categories.POST_DEPOT,
        "Post office": Categories.POST_OFFICE,
        "Postal agency": {"amenity": "post_office", "post_office": "post_partner"},  # 6 "vydejniMisto"
        "Service point": {"amenity": "post_office", "post_office": "post_partner"},  # 43 "vydejniMisto"
        "Technical outlet": {"amenity": "post_office", "post_office": "post_partner"},  # 252 "technickaProvozovna"
        "post.type.external.partner-box": Categories.PARCEL_LOCKER,  # "balikovna_box"
    }

    def parse(self, response, **kwargs):
        yield JsonRequest(
            url="https://www.postaonline.cz/en/vyhledat-pobocku?p_p_id=findpostoffice_WAR_findpostportlet&p_p_lifecycle=2&p_p_resource_id=preparePostForMap",
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)

            if cat := self.types.get(location["type"]):
                apply_category(cat, item)

            yield item
