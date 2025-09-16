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
        # Brussels has `<fr> - <nl>` convention for naming:
        # https://wiki.openstreetmap.org/wiki/WikiProject_Belgium/Conventions/Street_names

        fr_city = row.get("municipality_name_fr")
        nl_city = row.get("municipality_name_nl")
        if fr_city and nl_city:
            item["city"] = f"{fr_city} - {nl_city}"
        else:
            item["city"] = fr_city or nl_city

        fr_street = row.get("streetname_fr")
        nl_street = row.get("streetname_nl")
        if fr_street and nl_street:
            item["street"] = f"{fr_street} - {nl_street}"
        else:
            item["street"] = fr_street or nl_street

        fr_postname = row.get("postname_fr")
        nl_postname = row.get("postname_nl")
        if fr_postname and nl_postname:
            item["extras"]["addr:district"] = f"{fr_postname} - {nl_postname}"
        else:
            item["extras"]["addr:district"] = fr_postname or nl_postname

        return item
