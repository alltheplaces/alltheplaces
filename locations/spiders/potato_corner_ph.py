import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PotatoCornerPHSpider(scrapy.Spider):
    name = "potato_corner_ph"
    item_attributes = {
        "brand": "Potato Corner",
        "brand_wikidata": "Q60741625",
        "name": "Potato Corner",
        "extras": {"cuisine": "fries", "takeaway": "yes"},
    }
    no_refs = True
    # The store locator's front-end (https://potatocorner.com/store-locator/) reads its data
    # straight from this public Google Sheet via the Sheets API.
    start_urls = [
        "https://sheets.googleapis.com/v4/spreadsheets/1iH8hIahSJ5vjU_NWn2PD1HSex97iCuM-AcsLkEea4_w/values/STORE%20MAP?alt=json&key=AIzaSyD8838tK1fBuBpvn-BcyDliaNPZ8gIOtAg"
    ]

    def parse(self, response, **kwargs):
        rows = response.json()["values"]
        for row in rows[1:]:
            # Some rows are just region section headers with a name and nothing else.
            if len(row) < 5 or not (row[1] and row[2] and row[3] and row[4]):
                continue

            item = Feature()
            item["branch"] = row[1]
            item["addr_full"] = row[2]

            # A handful of rows in the source sheet have mistyped coordinates
            # (e.g. digits transposed, or a duplicated lat/lon pair) that land
            # outside the Philippines entirely, so sanity check before using them.
            try:
                lat, lon = float(row[3]), float(row[4])
                if 4 <= lat <= 21 and 116 <= lon <= 127:
                    item["lat"], item["lon"] = lat, lon
            except ValueError:
                pass

            apply_category(Categories.FAST_FOOD, item)

            yield item
