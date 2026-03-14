import io
import logging
import re

import pdfplumber
from scrapy import Spider

from locations.items import Feature

# Disable pdfplumber logging to avoid cluttering the output
logging.getLogger("pdfminer").setLevel(logging.WARNING)


class EcobulpackBGSpider(Spider):
    name = "ecobulpack_bg"
    item_attributes = {"operator": "Екобулпак", "operator_wikidata": "Q116687156"}
    allowed_domains = ["ecobulpack.bg"]
    start_urls = [
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Bankya-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Vitosha-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Vrabnitsa-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Vazrazhdane-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Izgrev-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Ilinden-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Krasna-polyana-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Kremikovtsi-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Lozenets-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Lyulin-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Ovcha-kupel-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Nadezhda-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Pancharevo-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Poduyane-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Serdika-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2025-Slatina-Spisak.pdf",
    ]
    no_refs = True

    def parse(self, response):
        with pdfplumber.open(io.BytesIO(response.body)) as pdf:
            rows = []
            for page in pdf.pages:
                tbl = page.extract_table()
                rows.extend(tbl)

            for row in rows[1:]:
                # skip headers and empty rows
                if len(row) < 7 or row[5] is None or row[5] == "" or re.search(r"^\d+\.\d+$", row[5]) is None:
                    continue

                # Some items have reversed lat/lon
                coords = [row[5], row[6]]
                map(float, coords)
                coords.sort(reverse=True)

                item = {
                    "street_address": row[2],
                    "lat": coords[0],
                    "lon": coords[1],
                }
                yield Feature(**item)
