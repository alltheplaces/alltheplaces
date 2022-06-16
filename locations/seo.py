import json
from typing import Iterator
from locations.items import GeojsonPointItem

name_keys = ["name", "title"]

street_address_keys = ["streetAddress", "street_address", "street-address"]

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

region_keys = ["addressRegion", "region", "state"]

country_keys = [
    "addressCountry",
    "country",
    "Country",
    "countryCode",
    "CountryCode",
    "country_code",
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


def get_key(src, keys):
    for key in keys:
        if src.get(key):
            return src.get(key)
    return None


def extract_field(item, dst_field, src, keys):
    src_data = get_key(src, keys)
    if src_data and isinstance(src_data, str):
        item[dst_field] = src_data.strip()
        return item[dst_field]
    return None


def extract_details(item, src) -> GeojsonPointItem:
    """
    Attempt to dig fields out of the src and assign to the common internal representation.
    It cannot possibly get things correct all of the time but picks up many standard field
    aliases to lighten the implementation effort in individual spiders, which are always
    able to pick up the fall out.
    """
    if src:
        extract_field(item, "name", src, name_keys)
        extract_field(item, "street_address", src, street_address_keys)
        extract_field(item, "city", src, city_keys)
        extract_field(item, "state", src, region_keys)
        extract_field(item, "country", src, country_keys)
        extract_field(item, "postcode", src, postcode_keys)
        extract_field(item, "email", src, email_keys)
        extract_field(item, "phone", src, phone_keys)
        extract_geo(item, src)
    return item


def extract_geo(item, src) -> GeojsonPointItem:
    if src:
        item.set_geo(get_key(src, lat_keys), get_key(src, lon_keys))
    return item


def extract_html_meta_details(item, response) -> GeojsonPointItem:
    """
    Pull certain meta properties from the page and form a dict from them to give
    to the generic extract code.
    """
    keys = response.xpath("/html/head/meta/@property").getall()
    src = {}
    for key in keys:
        if key.startswith("og:") or key.startswith("place:location:"):
            content = response.xpath(
                '//meta[@property="{}"]/@content'.format(key)
            ).get()
            if content:
                src[key.split(":")[-1]] = content
    extract_details(item, src)
    return item


def extract_ldjson(brand, response, required_type) -> Iterator[GeojsonPointItem]:
    scripts = response.xpath('//script[@type="application/ld+json"]//text()').getall()
    for script in scripts:
        entries = json.loads(script)
        for item in parse_ldjson(brand, entries, required_type, response):
            yield item


def ensure_list(x):
    """
    Return parameter as a single item list if it is not a list already, else return unchanged.
    """
    if not isinstance(x, list):
        return [x]
    return x


def get_first_key(src, lookup_key):
    """
    Get the first value matching a given key in nested object.
    """
    value = list(get_all_keys(src, lookup_key))
    return value[0] if value else None


def get_all_keys(src, lookup_key=None):
    """
    Get all the values matching a given key from a complex structure. Nested keys will not be split out.
    """
    if isinstance(src, dict):
        for k, v in src.items():
            if k == lookup_key:
                yield v
            elif not lookup_key and isinstance(v, str):
                yield v
            else:
                yield from get_all_keys(v, lookup_key)
    elif isinstance(src, list):
        for item in src:
            yield from get_all_keys(item, lookup_key)
    elif not lookup_key:
        yield src


def parse_ldjson(
    brand, entry_or_entries, required_type, response=None
) -> GeojsonPointItem:
    # Sometimes (hello Marriott in the first case) the entry array is one level down.
    if isinstance(entry_or_entries, dict):
        if entry_or_entries.get("@graph"):
            entry_or_entries = entry_or_entries.get("@graph")
        elif entry_or_entries.get("mainEntity"):
            # This was added for Radisson in the first instance
            entry_or_entries = entry_or_entries.get("mainEntity")

    for entry in ensure_list(entry_or_entries):
        # Look for an entry with the required type
        if required_type not in ensure_list(entry.get("@type")):
            continue

        if brand:
            item = brand.item(response)
        else:
            item = GeojsonPointItem()

        # Try an extract on the top level as some sites encode things upstairs rather than in sub elements.
        extract_details(item, entry)

        image_url = entry.get("image")
        if isinstance(image_url, dict):
            image_url = image_url.get("url")
        if image_url and isinstance(image_url, str) and image_url.startswith("http"):
            item["image"] = image_url

        # First we knock out any "parentOrganization" field which may have an embedded
        # address which we do not want the lookup code beyond this to pick up on.
        # Vets4Pets UK was the first instance that made this necessary.
        if entry.get("parentOrganization"):
            entry["parentOrganization"] = None

        address = get_first_key(entry, "address")
        if isinstance(address, list):
            # First saw VisionExpress have an array entry for the address, Vets4Pets also
            address = address[0]
        extract_details(item, address)

        item.set_source_data(response)["ld_json"] = entry

        yield extract_geo(item, entry.get("geo"))


def join_address_fields(src, *fields):
    """
    Pull referenced fields from the src and form a clean address string assuming comma separated address.
    Tolerant of missing and empty fields.
    """
    dirty = []
    for field in fields:
        dirty.append(src.get(field))
    return join_address_array(dirty)


def join_address_array(address_array, join_str=","):
    """
    Attempt to "clean" an array of address items returning a single string address.
    """
    address_array = list(filter(lambda s: s and len(s.strip()) > 0, address_array))
    all_parts = join_str.join(address_array).split(join_str)
    all_parts = list(filter(lambda s: s and len(s.strip()) > 0, all_parts))
    all_parts = list(map(lambda s: s.strip(), all_parts))
    for i in range(0, len(all_parts)):
        for j in range(i + 1, len(all_parts)):
            # Remove duplicate consecutive entries
            if (
                all_parts[i]
                and all_parts[j]
                and all_parts[i].lower() == all_parts[j].lower()
            ):
                all_parts[i] = None
    all_parts = list(filter(lambda s: s, all_parts))
    join_str = join_str + " "
    return join_str.join(all_parts)
