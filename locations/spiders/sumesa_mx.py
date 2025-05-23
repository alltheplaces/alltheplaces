from locations.spiders.la_comer_mx import LaComerMXSpider


class SumesaMXSpider(LaComerMXSpider):
    name = "sumesa_mx"
    item_attributes = {"brand": "Sumesa", "brand_wikidata": "Q123741153"}
    locations_key = ["listSumesa"]
