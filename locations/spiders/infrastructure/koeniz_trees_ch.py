from io import BytesIO
from typing import IO, Iterable, Tuple
from zipfile import ZipFile

import pyproj
from scrapy import Spider
from scrapy.http import Response
from shapefile import Reader, ShapeRecord

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class KoenizTreesCHSpider(Spider):
    name = "koeniz_trees_ch"
    allowed_domains = ["gisdoc.koeniz.ch"]
    dataset_attributes = Licenses.OPENDATA_SWISS_BY.value | {
        "name": "Gemeindegrün Baumkataster Gemeinde Köniz",
        "website": "https://opendata.swiss/de/dataset/gemeindegrun-baumkataster-gemeinde-koniz",
        "attribution:name:de": "Gemeinde Köniz",
        "attribution:name:en": "Municipality of Köniz",
        "contact:email": "geoportal@koeniz.ch",
    }
    start_urls = ["https://gisdoc.koeniz.ch/public/opendataswiss/baumkataster-shp.zip"]
    no_refs = True

    # Swiss LV95 (https://epsg.io/2056) -> WGS84 lat/lon (https://epsg.io/4326)
    coord_transformer = pyproj.Transformer.from_crs(2056, 4326)

    def parse(self, response: Response) -> Iterable[Feature]:
        with ZipFile(BytesIO(response.body)) as zf:
            with (
                self.open_part(zf, "shp") as shp,
                self.open_part(zf, "dbf") as dbf,
                self.open_part(zf, "shx") as shx,
            ):
                sf = Reader(shp=shp, dbf=dbf, shx=shx)
                for rec in sf.shapeRecords():
                    if coord := self.parse_coord(rec):
                        extras = self.parse_species(rec)
                        feature = Feature(lat=coord[0], lon=coord[1], extras=extras)
                        apply_category(Categories.NATURAL_TREE, feature)
                        yield feature

    def open_part(self, zf: ZipFile, extension: str) -> IO[bytes]:
        filename = next(f for f in zf.namelist() if f.lower().endswith(extension))
        return zf.open(filename)

    def parse_coord(self, rec: ShapeRecord) -> Tuple[float, float] | None:
        geometry = rec.__geo_interface__.get("geometry")
        if not geometry:
            return None
        c = geometry.get("coordinates")
        if c and len(c) >= 2:
            lat, lon = self.coord_transformer.transform(c[0], c[1])
            return (round(lat, 7), round(lon, 7))
        else:
            return None

    def parse_species(self, rec: ShapeRecord) -> dict[str, str]:
        props = rec.__geo_interface__["properties"]
        if not props:
            return {}
        sp = (props.get("d_ART") or "").split("(")[0].strip()
        sp = sp.replace(" x ", " × ")
        if len(sp) == 0 or sp in {"Andere", "Unbekannt"}:
            return {}
        genus = sp.split()[0]
        if " " in sp:
            return {"genus": genus, "species": sp}
        else:
            return {"genus": genus}
