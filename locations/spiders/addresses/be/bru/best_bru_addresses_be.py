from locations.items import Feature
from locations.spiders.addresses.be.best_addresses_be import BeSTAddressesBESpider


class BeSTBruAddressesBESpider(BeSTAddressesBESpider):
    name = "best_bru_addresses_be"
    dataset_attributes = {
        "attribution": "optional",
        "attribution:name": "Paradigm.brussels",
        "attribution:website": "https://datastore.brussels/web/data/dataset/a8c9ccde-5c2b-11ed-913a-900f0cda5d5c",
        "license": "Creative Commons Zero",
        "license:website": "https://creativecommons.org/publicdomain/zero/1.0/",
        "license:wikidata": "Q6938433",
        "attribution": "optional",
        "use:commercial": "permit",
    }
    region_urls = [
        "https://opendata.bosa.be/download/best/openaddress-bebru.zip",  # Brussels
    ]

    def post_process_item(self, item: Feature, row: dict) -> Feature:
        item["city"] = row.get("municipality_name_fr") or row.get("municipality_name_nl")
        item["street"] = row.get("streetname_fr") or row.get("streetname_nl")
        item["extras"]["addr:district"] = row.get("postname_fr") or row.get("postname_nl")
        return item

