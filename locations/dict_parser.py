from locations.items import GeojsonPointItem


class DictParser(object):

    ref_keys = ["ref", "id", "Id", "store_id", "shopNumber", "slug"]

    name_keys = ["name", "Name", "storeName", "displayName", "DisplayName", "title"]

    house_number_keys = ["houseNumber", "houseNo", "streetNumber"]

    street_address_keys = [
        "streetAddress",
        "street_address",
        "street-address",
        "addressLine1",
        "line1",
        "addressLineOne",
    ]

    city_keys = [
        "addressLocality",
        "city",
        "addressCity",
        "town",
        "Town",
        "CITY",
        "City",
        "locality",
    ]

    region_keys = ["addressRegion", "region", "state", "StateProvince"]

    country_keys = [
        "countryCode",
        "CountryCode",
        "country_code",
        "addressCountry",
        "country",
        "Country",
    ]

    postcode_keys = [
        "postalCode",
        "postCode",
        "postalcode",
        "zip",
        "Postcode",
        "postcode",
        "post_code",
        "addressPostCode",
        "PostCode",
        "postal",
        "postal_code",
        "POSTCODE",
        "PostalCode",
        "Zip",
        "ZIP",
        "ZipCode",
        "zipCode",
        "zipcode",
    ]

    email_keys = ["Email", "email", "ContactEmail", "EMAIL"]

    phone_keys = [
        "phoneNumber",
        "phone",
        "telephone",
        "Telephone",
        "tel",
        "telephoneNumber",
        "Telephone1",
        "contactNumber",
        "PhoneNumber",
        "PHONE",
        "Phone",
        "phone_number",
        "phoneNo",
    ]

    lat_keys = [
        "latitude",
        "lat",
        "Lat",
        "LAT",
        "Latitude",
        "displayLat",
        "yextDisplayLat",
    ]

    lon_keys = [
        "longitude",
        "lon",
        "long",
        "Lng",
        "LON",
        "lng",
        "Longitude",
        "displayLng",
        "yextDisplayLng",
    ]

    @staticmethod
    def parse(obj) -> GeojsonPointItem:
        item = GeojsonPointItem()

        item["ref"] = DictParser.get_first_key(obj, DictParser.ref_keys)
        item["name"] = DictParser.get_first_key(obj, DictParser.name_keys)

        location = DictParser.get_first_key(obj, ["location", "geolocation", "geo"])
        # If not a good location object then use the parent
        if not location or not isinstance(location, dict):
            location = obj
        item["lat"] = DictParser.get_first_key(location, DictParser.lat_keys)
        item["lon"] = DictParser.get_first_key(location, DictParser.lon_keys)

        address = DictParser.get_first_key(obj, ["address", "addr"])

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
            if obj.get(key):
                return obj[key]
            elif obj.get(key.lower()):
                return obj[key.lower()]
            elif obj.get(key.upper()):
                return obj[key.upper()]

    # Looks for a nested key and return the value.
    @staticmethod
    def get_nested_key(obj, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    return v
                val = DictParser.get_nested_key(v, key)
                if val:
                    return val
        return None
