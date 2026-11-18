import csv
import io
import zipfile
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class CorreosMailboxesESSpider(Spider):
    name = "correos_mailboxes_es"
    item_attributes = {"operator": "Correos", "operator_wikidata": "Q776605"}
    allowed_domains = ["descargas.correos.es", "api1.correos.es"]
    # The office finder at https://www.correos.es/es/es/herramientas/oficinas-buzones-citypaq returns letter
    # boxes too. It needs the client id, secret and subscription key written into the site's own script.
    API = "https://api1.correos.es/digital-services/searchloc/api/v1/offices"
    HEADERS = {
        "client_id": "988eca84fe054a8496963855225f17bd",
        "client_secret": "8384992f133B4639B95920695Adf59Ff",
        "Ocp-Apim-Subscription-Key": "981d0e4f0a064cbdbf32e04ef0b4426b",
        "Origin": "https://www.correos.es",
        "Referer": "https://www.correos.es/",
    }
    # The search takes a postcode or address (not coordinates) and returns at most the nearest 2,000 boxes.
    # Searching around every postcode that has a Correos office or rural service point (from Correos' daily
    # office file) covers towns and villages alike; boxes found by several searches are deduplicated by id.
    RADIUS_M = 15000
    start_urls = ["https://descargas.correos.es/Publico/conviert/Oficinas.zip"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
            name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
            rows = csv.DictReader(io.StringIO(archive.read(name).decode("utf-8")), delimiter=";")
            postcodes = sorted({row["LOCALIZACION CP"] for row in rows if row["LOCALIZACION CP"]})
        self.crawler.stats.set_value("atp/correos_mailboxes_es/postcodes", len(postcodes))
        for postcode in postcodes:
            yield JsonRequest(
                f"{self.API}?text={postcode}&searchType=otros&distance={self.RADIUS_M}",
                headers=self.HEADERS,
                callback=self.parse_boxes,
            )

    def parse_boxes(self, response: Response) -> Any:
        boxes = (response.json().get("others") or {}).get("mailboxes") or []
        if len(boxes) >= 2000:
            self.crawler.stats.inc_value("atp/correos_mailboxes_es/saturated_search")
        for box in boxes:
            if not box.get("active"):
                continue
            item = Feature()
            item["ref"] = box["mailboxId"]
            item["lat"], item["lon"] = box["latitude"], box["longitude"]
            item["street_address"] = box.get("address")
            item["postcode"] = box.get("postalCode")
            item["city"] = box.get("cityName")
            item["state"] = box.get("provinceName")
            apply_category(Categories.POST_BOX, item)
            yield item
