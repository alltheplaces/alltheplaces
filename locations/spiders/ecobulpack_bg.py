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
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Bankya-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Vitosha-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Vrabnitsa-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Vazrazhdane-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Izgrev-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Ilinden-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Krasna-polyana-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Kremikovtsi-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Lozenets-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Lyulin-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Ovcha-kupel-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Nadezhda-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Pancharevo-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Poduyane-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Serdika-Spisak.pdf",
        "https://www.ecobulpack.bg/files/obshtini/stolichna/2026-Slatina-Spisak.pdf",
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
