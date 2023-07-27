from locations.items import Feature


class DictParser:
    ref_keys = ["ref", "id", "store-id", "storeID", "storeNumber", "shop-number", "LocationID", "slug", "storeCode"]

    name_keys = ["name", "store-name", "display-name", "title", "businessName"]

    house_number_keys = ["house-number", "house-no", "street-number", "street-no", "address-street-no"]

    street_address_keys = [
        # EN
        "street-address",
        "address1",
        "address-line1",
        "line1",
        "address-line-one",
        # JP
        "町域以下住所",  # "address below town limits"
    ]

    city_keys = [
        # EN
        "address-locality",
        "city",
        "address-city",
        "town",
        "locality",
        "suburb",
        "city-name",
        # JP
        "市区町村",  # "municipality"
    ]

    region_keys = [
        # EN
        "address-region",
        "region",
        "state",
        "state-province",
        "province",
        "state-code",
        "county",
        "state-name",
        # JP
        "都道府県",  # "prefecture"
    ]

    country_keys = [
        "country-code",
        "address-country",
        "country",
        "country-name",
    ]

    isocode_keys = [
        "iso-code",
    ]

    postcode_keys = [
        # EN
        "postal-code",
        "post-code",
        "postcode",
        "zip",
        "zipcode",
        "address-post-code",
        "postal",
        "zip-code",
        "address-postal-code",
        # JP
        "郵便番号",  # "post code"
    ]

    email_keys = ["email", "contact-email", "email-address", "email1"]

    phone_keys = [
        "phone-number",
        "phone",
        "telephone",
        "tel",
        "telephone-number",
        "telephone1",
        "contact-number",
        "phone-no",
        "contact-phone",
    ]

    lat_keys = [
        "latitude",
        "lat",
        "display-lat",
        "yext-display-lat",
        "mapLatitude",
        "geoLat",
    ]

    lon_keys = [
        "longitude",
        "lon",
        "long",
        "lng",
        "display-lng",
        "yext-display-lng",
        "mapLongitude",
        "geoLng",
    ]

    website_keys = ["url", "website", "permalink", "store-url", "storeURL", "website-url", "websiteURL"]

    @staticmethod
    def parse(obj) -> Feature:
        item = Feature()

        item["ref"] = DictParser.get_first_key(obj, DictParser.ref_keys)
        item["name"] = DictParser.get_first_key(obj, DictParser.name_keys)

        location = DictParser.get_first_key(
            obj, ["location", "geo-location", "geo", "geo-point", "geocodedCoordinate", "coordinates"]
        )
        # If not a good location object then use the parent
        if not location or not isinstance(location, dict):
            location = obj
        item["lat"] = DictParser.get_first_key(location, DictParser.lat_keys)
        item["lon"] = DictParser.get_first_key(location, DictParser.lon_keys)

        address = DictParser.get_first_key(obj, ["address", "addr", "storeaddress", "physicalAddress"])

        if address and isinstance(address, str):
            item["addr_full"] = address

        if not address or not isinstance(address, dict):
            address = obj

        item["housenumber"] = DictParser.get_first_key(address, DictParser.house_number_keys)
        item["street"] = DictParser.get_first_key(address, ["street", "street-name"])
        item["street_address"] = DictParser.get_first_key(address, DictParser.street_address_keys)
        item["city"] = DictParser.get_first_key(address, DictParser.city_keys)
        item["state"] = DictParser.get_first_key(address, DictParser.region_keys)
        item["postcode"] = DictParser.get_first_key(address, DictParser.postcode_keys)

        country = DictParser.get_first_key(address, DictParser.country_keys)
        if country and isinstance(country, dict):
            isocode = DictParser.get_first_key(country, DictParser.isocode_keys)
            if isocode and isinstance(isocode, str):
                item["country"] = isocode
            # TODO: Handle other potential country fields inside the dict?
        else:
            item["country"] = country

        contact = DictParser.get_first_key(obj, ["contact"])
        if not contact or not isinstance(contact, dict):
            contact = obj

        item["email"] = DictParser.get_first_key(contact, DictParser.email_keys)
        item["phone"] = DictParser.get_first_key(contact, DictParser.phone_keys)
        item["website"] = DictParser.get_first_key(contact, DictParser.website_keys)

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
        results = set()
        results.add(key)

        lower = key.lower()
        results.add(lower)

        upper = key.upper()
        results.add(upper)

        title = key.title()
        results.add(title)

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

    @staticmethod
    def get_nested_key(obj, key):
        """
        Return value for first matching key in an object, traversing lists and dicts.
        :param obj: the object to traverse
        :param key: the key to match
        :return: the first matching value, or None
        """
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    return v
                if val := DictParser.get_nested_key(v, key):
                    return val
        elif isinstance(obj, list):
            for x in obj:
                if val := DictParser.get_nested_key(x, key):
                    return val
        return None

    @staticmethod
    def iter_matching_keys(obj, key):
        """
        An iterator for values for all matching keys in an object, traversing lists and dicts.
        :param obj: the object to traverse
        :param key: the key to match
        :return: value iterator for all matching keys
        """
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    yield v
                else:
                    yield from DictParser.iter_matching_keys(v, key)
        elif isinstance(obj, list):
            for x in obj:
                yield from DictParser.iter_matching_keys(x, key)
