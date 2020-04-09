# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from xlrd import open_workbook


class TAPetroSpider(scrapy.Spider):
    name = 'tapetro'
    item_attributes = { 'brand': "TravelCenters of America", 'brand_wikidata': "Q7835892" }
    allowed_domains = ['www.ta-petro.com']
    start_urls = (
        'http://www.ta-petro.com/assets/ce/Documents/Master-Location-List.xls',
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
                if value:
                  store[column] = value

            if store.get("LATITUDE") is None or store.get("LONGITUDE") is None:
                continue

            ref = '%s-%s-%s' % (
                store['SITE ID#'], store['BRAND'], store['LOCATION_ID'])
            yield GeojsonPointItem(
                ref=ref,
                name=store['LOCATION'],
                addr_full=store['ADDRESS'],
                city=store['CITY'],
                state=store['STATE'],
                postcode=store['ZIPCODE'],
                phone=store['PHONE'],
                lat=float(store['LATITUDE']),
                lon=float(store['LONGITUDE']),
            )
