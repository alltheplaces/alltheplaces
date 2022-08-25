from locations.items import GeojsonPointItem


class DictParser(object):
    @staticmethod
    def parse(obj) -> GeojsonPointItem:
        item = GeojsonPointItem()

        location = DictParser.get_first_key(obj, ["location", "geolocation"])

        # If not a good location object then use the parent
        if not location or not isinstance(location, dict):
            location = obj

        item["lat"] = DictParser.get_first_key(location, ["latitude", "lat"])
        item["lon"] = DictParser.get_first_key(
            location, ["longitude", "lon", "long", "lng"]
        )

        item["name"] = DictParser.get_first_key(
            obj, ["name", "storeName", "displayName"]
        )

        address = DictParser.get_first_key(obj, ["address", "addr"])

        if address and isinstance(address, str):
            item["addr_full"] = address

        if not address or not isinstance(address, dict):
            address = obj

        item["housenumber"] = DictParser.get_first_key(
            address, ["houseNumber", "houseNo", "streetNumber"]
        )
        item["street"] = DictParser.get_first_key(address, ["street", "streetName"])
        item["street_address"] = DictParser.get_first_key(
            address, ["streetAddress", "street_address", "line1"]
        )

        item["city"] = DictParser.get_first_key(address, ["city", "town"])
        item["state"] = DictParser.get_first_key(address, ["state", "region"])
        item["postcode"] = DictParser.get_first_key(
            address, ["postCode", "post_code", "postalCode"]
        )
        item["country"] = DictParser.get_first_key(address, ["country", "countryCode"])

        contact = DictParser.get_first_key(obj, ["contact"])

        if not contact or not isinstance(contact, dict):
            contact = obj

        item["phone"] = DictParser.get_first_key(contact, ["phone", "telephone", "tel"])

        item["ref"] = DictParser.get_first_key(
            obj, ["ref", "id", "store_id", "shopNumber", "slug"]
        )

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
