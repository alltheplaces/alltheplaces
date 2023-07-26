import pyproj
import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


# Open Data of the City of Winterthur, Switzerland
class WinterthurCHSpider(scrapy.Spider):
    name = "winterthur_ch"
    allowed_domains = ["stadtplantest.winterthur.ch"]
    dataset_attributes = {
        "attribution": "optional",
        "attribution:name:de": "Stadt Winterthur",
        "attribution:name:en": "City of Winterthur",
        "attribution:wikidata": "Q9125",
        "license": "Creative Commons Zero",
        "license:website": "https://stadtplantest.winterthur.ch/stadtgruen/spielplatzkontrolle-service/swagger/index.html",
        "license:wikidata": "Q6938433",
    }

    def start_requests(self):
        yield scrapy.Request(
            "https://stadtplantest.winterthur.ch/stadtgruen/spielplatzkontrolle-service/collections/playgrounds/items/",
            callback=self.parse_playgrounds,
        )

    def parse_playgrounds(self, response):
        abbrevs = {
            "KG": "Kindergarten",
            "SH": "Schulhaus",
        }
        # Swiss LV95 (https://epsg.io/2056) -> lat/lon (https://epsg.io/4326)
        coord_transformer = pyproj.Transformer.from_crs(2056, 4326)
        for f in response.json():
            props = f["properties"]
            coords = f["geometry"].get("coordinates", [])
            if len(coords) < 2:
                continue
            lat, lon = coord_transformer.transform(coords[0], coords[1])
            ref = str(props.get("fid"))
            if props.get("nummer") > 0:
                ref = str(props["nummer"])
            item = {
                "lat": lat,
                "lon": lon,
                "ref": ref,
                "extras": {
                    "operator": "Stadtgrün Winterthur",
                    "operator:wikidata": "Q56825906",
                },
            }
            apply_category(Categories.LEISURE_PLAYGROUND, item)
            if name_words := props.get("name", "").split():
                name_words[0] = abbrevs.get(name_words[0], name_words[0])
                item["name"] = " ".join(name_words)
            yield Feature(**item)
