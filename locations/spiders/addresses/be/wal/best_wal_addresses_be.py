from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.be.best_addresses_be import BeSTAddressesBESpider


class BeSTWalAddressesBESpider(BeSTAddressesBESpider):
    name = "best_wal_addresses_be"
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Service public de Wallonie (SPW) - ICAR - Points d'adresses",
        "attribution:website": "https://geodata.wallonie.be/id/2998bccd-dae4-49fb-b6a5-867e6c37680f",
        "use:commercial": "permit",
    }
    region_urls = [
        "https://opendata.bosa.be/download/best/openaddress-bewal.zip",  # Wallonia
    ]

    def post_process_item(self, item: Feature, row: dict) -> Feature:
        item["city"] = row.get("municipality_name_fr")
        item["street"] = row.get("streetname_fr")
        item["extras"]["addr:district"] = row.get("postname_fr")
        return item
