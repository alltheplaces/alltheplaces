# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from xlrd import open_workbook

BRANDS = {"T": "TravelCenters of America", "P": "Petro", "TE": "TA Express"}


class TAPetroSpider(scrapy.Spider):
    name = "tapetro"
    item_attributes = {
        "brand": "TravelCenters of America",
        "brand_wikidata": "Q7835892",
    }
    allowed_domains = ["www.ta-petro.com"]
    start_urls = (
        "http://www.ta-petro.com/assets/ce/Documents/Master-Location-List.xls",
    )

    def parse(self, response):
        workbook = open_workbook(file_contents=response.body)
        sheet = workbook.sheets()[0]  # Sheet1

        # read header
        nrow = 0
        columns = []
        for ncol in range(sheet.ncols):
            columns.append((ncol, sheet.cell(nrow, ncol).value))

        for nrow in range(1, sheet.nrows):
            store = {}
            for ncol, column in columns:
                value = sheet.cell(nrow, ncol).value
                store[column] = value

            if not (store.get("LATITUDE") and store.get("LONGITUDE")):
                continue

            ref = "%s-%s-%s" % (store["SITE ID#"], store["BRAND"], store["LOCATION_ID"])
            yield GeojsonPointItem(
                ref=ref,
                lat=float(store["LATITUDE"]),
                lon=float(store["LONGITUDE"]),
                name=store["LOCATION"],
                addr_full=store["ADDRESS"],
                city=store["CITY"],
                state=store["STATE"],
                postcode=store["ZIPCODE"],
                phone=store["PHONE"],
                brand=BRANDS.get(store["BRAND"], BRANDS["T"]),
                extras={
                    "amenity:fuel": True,
                    "fuel:diesel:class2": store["WINTERIZED DIESEL NOV-MAR(any temp)"]
                    == "Y"
                    or store[
                        "WINTERIZED DIESEL NOV-MAR (when temps are 10 degrees or below)"
                    ]
                    == "Y"
                    or store[
                        "WINTERIZED DIESEL NOV-MAR (when temps are 30 degrees or below)"
                    ]
                    == "y",
                    "fuel:diesel": True,
                    "fuel:HGV_diesel": True,
                    "fuel:lng": store["LNG(Liquified Natural Gas)"] == "Y",
                    "fuel:propane": store["PROPANE"] == "Y",
                    "hgv": True,
                },
            )
