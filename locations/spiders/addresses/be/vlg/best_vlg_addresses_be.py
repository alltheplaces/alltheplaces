from locations.items import Feature
from locations.licenses import Licenses
from locations.spiders.addresses.be.best_addresses_be import BeSTAddressesBESpider


class BeSTVlgAddressesBESpider(BeSTAddressesBESpider):
    name = "best_vlg_addresses_be"
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Digitaal Vlaanderen",
        "attribution:website": "https://www.vlaanderen.be/digitaal-vlaanderen/onze-diensten-en-platformen/gebouwen-en-adressenregister#het-adressenregister",
        "use:commercial": "permit",
    }
    region_urls = [
        "https://opendata.bosa.be/download/best/openaddress-bevlg.zip",  # Flanders
    ]

    def post_process_item(self, item: Feature, row: dict) -> Feature:
        item["city"] = row.get("municipality_name_nl")
        item["street"] = row.get("streetname_nl")
        item["extras"]["addr:district"] = row.get("postname_nl")
        return item
