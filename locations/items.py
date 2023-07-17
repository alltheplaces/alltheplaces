# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Feature(scrapy.Item):
    _validation = scrapy.Field()

    lat = scrapy.Field()
    lon = scrapy.Field()
    geometry = scrapy.Field()
    name = scrapy.Field()
    addr_full = scrapy.Field()
    housenumber = scrapy.Field()
    street = scrapy.Field()
    street_address = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    postcode = scrapy.Field()
    country = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    website = scrapy.Field()
    twitter = scrapy.Field()
    facebook = scrapy.Field()
    opening_hours = scrapy.Field()
    image = scrapy.Field()
    ref = scrapy.Field()
    brand = scrapy.Field()
    brand_wikidata = scrapy.Field()
    located_in = scrapy.Field()
    located_in_wikidata = scrapy.Field()
    nsi_id = scrapy.Field()
    extras = scrapy.Field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._values.get("extras"):
            self.__setitem__("extras", {})


def get_lat_lon(item: Feature) -> (float, float):
    if geometry := item.get("geometry"):
        if isinstance(geometry, dict):
            if geometry.get("type") == "Point":
                if coords := geometry.get("coordinates"):
                    try:
                        return float(coords[1]), float(coords[0])
                    except (TypeError, ValueError):
                        item["geometry"] = None
    else:
        try:
            return float(item.get("lat")), float(item.get("lon"))
        except (TypeError, ValueError):
            pass
    return None


def set_lat_lon(item: Feature, lat: float, lon: float):
    item["lat"] = None
    item["lon"] = None
    if lat and lon:
        item["geometry"] = {
            "type": "Point",
            "coordinates": [lon, lat],
        }
    else:
        item["geometry"] = None
