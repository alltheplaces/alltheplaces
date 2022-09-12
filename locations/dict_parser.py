from locations.items import GeojsonPointItem


class DictParser(object):

    ref_keys = ["ref", "id", "store-id", "shop-number", "slug"]

    name_keys = ["name", "store-name", "display-name", "title"]

    house_number_keys = ["house-number", "house-no", "street-number"]

    street_address_keys = [
        "address1",
        "street-address",
        "address-line1",
        "line1",
        "address-line-one",
    ]

    city_keys = [
        "address-locality",
        "city",
        "address-city",
        "town",
        "locality",
    ]

    region_keys = ["address-region", "region", "state", "state-province", "province"]

    country_keys = [
        "country-code",
        "address-country",
        "country",
        "country-name",
    ]

    postcode_keys = [
        "postal-code",
        "post-code",
        "zip",
        "zipcode",
        "address-post-code",
        "postal",
        "zip-code",
    ]

    email_keys = ["email", "contact-email"]

    phone_keys = [
        "phone-number",
        "phone",
        "telephone",
        "tel",
        "telephone-number",
        "telephone1",
        "contact-number",
        "phone-no",
    ]

    lat_keys = [
        "latitude",
        "lat",
        "display-lat",
        "yext-display-lat",
    ]

    lon_keys = [
        "longitude",
        "lon",
        "long",
        "lng",
        "display-lng",
        "yext-display-lng",
    ]

    @staticmethod
    def parse(obj) -> GeojsonPointItem:
        item = GeojsonPointItem()

        item["ref"] = DictParser.get_first_key(obj, DictParser.ref_keys)
        item["name"] = DictParser.get_first_key(obj, DictParser.name_keys)

        location = DictParser.get_first_key(
            obj, ["location", "geo-location", "geo", "geo-point"]
        )
        # If not a good location object then use the parent
        if not location or not isinstance(location, dict):
            location = obj
        item["lat"] = DictParser.get_first_key(location, DictParser.lat_keys)
        item["lon"] = DictParser.get_first_key(location, DictParser.lon_keys)

        address = DictParser.get_first_key(obj, ["address", "addr", "storeaddress"])

        if address and isinstance(address, str):
            item["addr_full"] = address

        if not address or not isinstance(address, dict):
            address = obj

        item["housenumber"] = DictParser.get_first_key(
            address, DictParser.house_number_keys
        )
        item["street"] = DictParser.get_first_key(address, ["street", "streetName"])
        item["street_address"] = DictParser.get_first_key(
            address, DictParser.street_address_keys
        )
        item["city"] = DictParser.get_first_key(address, DictParser.city_keys)
        item["state"] = DictParser.get_first_key(address, DictParser.region_keys)
        item["postcode"] = DictParser.get_first_key(address, DictParser.postcode_keys)
        item["country"] = DictParser.get_first_key(address, DictParser.country_keys)

        contact = DictParser.get_first_key(obj, ["contact"])
        if not contact or not isinstance(contact, dict):
            contact = obj
        # TODO: support e-mail in item structure
        # item["email"] = DictParser.get_first_key(contact, DictParser.email_keys)
        item["phone"] = DictParser.get_first_key(contact, DictParser.phone_keys)

        return item

    @staticmethod
    def get_first_key(obj, keys):
        for key in keys:
            variations = DictParser.get_variations(key)
            for variation in variations:
                if obj.get(variation):
                    return obj[variation]

    @staticmethod
    def get_variations(key):
        results = set(key)

        lower = key.lower()
        results.add(lower)

        upper = key.upper()
        results.add(upper)

        flatcase = key.lower().replace("-", "")
        results.add(flatcase)

        FLATCASEUPPER = flatcase.upper()
        results.add(FLATCASEUPPER)

        camelCase = key[0].lower()
        i = 1
        while i < len(key):
            if key[i] == "-":
                i += 1
                camelCase += key[i].upper()
            else:
                camelCase += key[i]
            i += 1

        results.add(camelCase)

        PascalCase = camelCase[0].upper() + camelCase[1:]

        results.add(PascalCase)

        snake_case = key.lower().replace("-", "_")
        results.add(snake_case)

        SCREAMING_SNAKE_CASE = key.upper().replace("-", "_")
        results.add(SCREAMING_SNAKE_CASE)

        camel_Snake_Case = key[0].lower()
        i = 1
        while i < len(key):
            if key[i] == "-":
                i += 1
                camel_Snake_Case += "_"
                camel_Snake_Case += key[i].upper()
            else:
                camel_Snake_Case += key[i]
            i += 1

        results.add(camel_Snake_Case)

        Pascal_Snake_Case = camel_Snake_Case[0].upper() + camel_Snake_Case[1:]

        results.add(Pascal_Snake_Case)

        return results

    # Looks for a nested key and return the value.
    @staticmethod
    def get_nested_key(obj, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    return v
                if val := DictParser.get_nested_key(v, key):
                    return val
        return None
