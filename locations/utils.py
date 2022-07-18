import json


def find_linked_data(response, wanted_type) -> {}:
    lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
    for ld in lds:
        ld_obj = json.loads(ld)

        if not ld_obj.get("@type"):
            continue

        types = ld_obj["@type"]

        if not isinstance(types, list):
            types = [types]

        if wanted_type in types:
            return ld_obj
