import re

from scrapy import Spider
from unidecode import unidecode

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class PaczkomatInpostPLSpider(Spider):
    name = "paczkomat_inpost_pl"
    item_attributes = {"brand": "Paczkomat InPost", "brand_wikidata": "Q110970254"}
    allowed_domains = ["inpost.pl"]
    start_urls = ["https://inpost.pl/sites/default/files/points.json"]

    def parse(self, response, **kwargs):
        for poi in response.json()["items"]:
            # Skip non-active locations and places which are not parcel lockers
            if poi["s"] != 1 and poi["t"] != 1 or poi["n"].startswith("POP-"):
                continue

            item = Feature()
            # The mapping is available in "load" js function of inpostLocatorMap object

            item["ref"] = poi["n"]
            item["name"] = poi["d"]
            item["city"] = poi["c"]
            item["street"] = poi["e"]
            item["state"] = poi["r"]
            item["postcode"] = poi["o"]
            item["housenumber"] = poi["b"]
            item["lat"] = poi["l"]["a"]
            item["lon"] = poi["l"]["o"]

            item["image"] = f'https://geowidget.easypack24.net/uploads/pl/images/{item["ref"]}.jpg'

            # TODO: figure out if below could be mapped
            # poi["m"]  # apm_doubled
            # poi["q"]  # partner_id
            # poi["f"]  # physical_type_mapped
            # poi["g"]
            # poi["p"]  # payment

            self.parse_slug(item)
            if poi["h"] == "24/7":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(poi["h"], days=DAYS_PL)
            yield item

    def parse_slug(self, item):
        slug_parts = ["paczkomat", item["city"], item["ref"], item["street"], "paczkomaty", item["state"]]
        slug = "-".join(map(lambda x: unidecode(x.lower().strip()), slug_parts))
        slug = re.sub(r"[·/_:; ]", "-", slug)
        slug = re.sub(r"[^a-z0-9 -]", "", slug)
        slug = re.sub(r"-+", "-", slug)
        item["website"] = f"https://inpost.pl/{slug}"
