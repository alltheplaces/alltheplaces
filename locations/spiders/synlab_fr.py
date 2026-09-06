import re

import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class SynlabFRSpider(JSONBlobSpider):
    name = "synlab_fr"
    item_attributes = {
        "brand": "Synlab",
        "brand_wikidata": "Q106847432",
    }
    start_urls = ["https://www.synlab.fr/trouver-un-laboratoire/"]

    def extract_json(self, response):
        data = response.xpath('//script[contains(text(), "const villes = ")]/text()').get()
        if data is not None:
            return chompjs.parse_js_object(data.split("const villes =")[1])

    def pre_process_data(self, location):
        location["name"] = location.pop("nom", None)
        location["addr_full"] = location.pop("adresse", None)

    def post_process_item(self, item, response, location):
        apply_category(Categories.MEDICAL_LABORATORY, item)
        name = item.pop("name", "").lower()

        phone = item.get("phone") or ""
        if "ou" in phone or "--" in phone:
            item["phone"] = phone.split("ou")[0].split("--")[0]

        if name.startswith("synlab"):
            item["branch"] = (
                (
                    name.removeprefix("synlab ")
                    .removeprefix("auvergne")
                    .removeprefix("biofrance")
                    .removeprefix("bioliance")
                    .removeprefix("bionyval")
                    .removeprefix("biopaj")
                    .removeprefix("bourgogne")
                    .removeprefix("carron")
                    .removeprefix("charentes")
                    .removeprefix("delaporte")
                    .removeprefix("hauts-de-france")
                    .removeprefix("midi")
                    .removeprefix("nord de france")
                    .removeprefix("normandie maine")
                    .removeprefix("normandie")
                    .removeprefix("nouvelle aquitaine")
                    .removeprefix("occitanie")
                    .removeprefix("oxabio")
                    .removeprefix("paris")
                    .removeprefix("provence")
                    .removeprefix("rhône-alpes")
                    .removeprefix("sud-ouest")
                    .removeprefix("normandie")
                    .removeprefix("normandie")
                )
                .strip(" -")
                .removeprefix("site")
            )
        elif name.startswith("laboratoire bioalliance"):
            item["branch"] = name.removeprefix("laboratoire bioalliance ").removeprefix("de ").removeprefix("d'")

        item["addr_full"] = location.pop("addr_full", "").split("(")[0]

        match = re.search(r"\b\d{5}\b", item.get("addr_full") or "")
        item["postcode"] = match.group() if match else None

        yield item
