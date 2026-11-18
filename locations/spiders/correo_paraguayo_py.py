import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class CorreoParaguayoPYSpider(Spider):
    name = "correo_paraguayo_py"
    # Dirección Nacional de Correos del Paraguay (DINACOPA); no Wikidata item.
    item_attributes = {"operator": "Correo Paraguayo"}
    allowed_domains = ["correoparaguayo.gov.py", "www.google.com"]
    # The "Agencias" page embeds a Google My Maps map made by DINACOPA ("Agencias y Sucursales de la DINACOPA");
    # its KML export holds every office as a placemark.
    start_urls = ["https://correoparaguayo.gov.py/sitio/agencias/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        embed = response.xpath('//iframe[contains(@src, "google.com/maps/d/")]/@src').get()
        map_id = parse_qs(urlparse(embed).query)["mid"][0]
        yield response.follow(f"https://www.google.com/maps/d/kml?mid={map_id}&forcekml=1", callback=self.parse_kml)

    def parse_kml(self, response: Response) -> Any:
        response.selector.remove_namespaces()
        for placemark in response.xpath("//Placemark"):
            name = re.sub(r"\s+", " ", placemark.xpath("name/text()").get() or "").strip()
            lon, lat = placemark.xpath("Point/coordinates/text()").get().strip().split(",")[:2]

            item = Feature()
            # "Sucursal Villa Hayes" is in the map twice; the duplicate ref is dropped by the pipeline.
            item["ref"] = re.sub(r"\W+", "-", name.lower()).strip("-")
            # The map was made from a spreadsheet that turned abbreviation dots into commas: "Juan E, Oleary".
            item["branch"] = re.sub(r"^Sucursal\s+", "", name.replace(", ", ". "))
            item["lat"], item["lon"] = lat, lon
            apply_category(Categories.POST_OFFICE, item)
            yield item
