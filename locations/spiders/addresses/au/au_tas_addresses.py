from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuTasAddressesSpider(ArcGISFeatureServerSpider, AddressSpider):
    name = "au_tas_addresses"
    host = "services.thelist.tas.gov.au"
    context_path = "arcgis"
    service_id = "Public/CadastreAndAdministrative"
    server_type = "MapServer"
    layer_id = "43"
    field_names = [
        "PID",
        "UNIT_NUMB",
        "ST_NO_FROM",
        "NO1_SUFFIX",
        "ST_NO_TO",
        "NO2_SUFFIX",
        "STREET",
        "ST_TYPE",
        "ST_SUFFIX",
        "LOCALITY",
        "POSTCODE",
    ]
    item_attributes = {"state": "TAS", "country": "AU"}
    dataset_attributes = Licenses.CCBY3AU.value | {
        "attribution:name": "State of Tasmania",
        "attribution:website": "https://www.thelist.tas.gov.au/app/content/data/geo-meta-data-record?detailRecordUID=403743d1-4d87-4fa4-8a51-91928f5935d6;https://www.thelist.tas.gov.au/app/content/the-list/news_and_information/resources/ilsdataattributionguidelines.pdf",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["PID"])

        if unit_number := feature.get("UNIT_NUMB"):
            item["extras"]["addr:unit"] = f"{unit_number}"

        housenumber_from = feature.get("ST_NO_FROM")
        if housenumber_from_suffix := feature.get("NO1_SUFFIX"):
            housenumber_from = f"{housenumber_from}{housenumber_from_suffix}"
        else:
            housenumber_from = f"{housenumber_from}"
        if housenumber_to := feature.get("ST_NO_TO"):
            if housenumber_to_suffix := feature.get("NO2_SUFFIX"):
                housenumber_to = f"{housenumber_to}{housenumber_to_suffix}"
            else:
                housenumber_to = f"{housenumber_to}"
            item["housenumber"] = f"{housenumber_from}-{housenumber_to}"
        else:
            item["housenumber"] = f"{housenumber_from}"

        street_name = feature.get("STREET")
        street_type = feature.get("ST_TYPE")
        street_suffix = feature.get("ST_SUFFIX")
        item["street"] = " ".join(filter(None, [street_name, street_type, street_suffix]))

        item["city"] = feature["LOCALITY"]
        item["postcode"] = str(feature["POSTCODE"])

        yield item
