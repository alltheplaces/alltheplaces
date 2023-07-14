from locations.storefinders.localisr import LocalisrSpider


class TradelinkAUSpider(LocalisrSpider):
    name = "tradelink_au"
    item_attributes = {"brand": "Tradelink", "brand_wikidata": "Q120648432"}
    api_key = "XV96QEW9G3X685YVP1N0RMEZKD74JRQ20O4O75J"
    search_coordinates = [
        (-35.286692, 149.116667),  # ACT
        (-34.0643261, 150.7872812),  # NSW
        (-24.720997, 146.912716),  # QLD
        (-14.063958, 132.865671),  # NT
        (-30.681651, 135.062477),  # SA
        (-42.08649, 146.796597),  # TAS
        (-37.189167, 144.623059),  # VIC
        (-30.759026, 117.753404),  # WA
    ]
