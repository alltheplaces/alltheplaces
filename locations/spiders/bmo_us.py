from locations.spiders.bmo_ca import BmoCASpider


class BmoUSSpider(BmoCASpider):
    name = "bmo_us"
    item_attributes = {"brand": "BMO", "brand_wikidata": "Q4835981"}
    api_brand_name = "bmoharrisusbranches"
    api_key = "6764F736-933E-4FE8-A5A8-A0F0196954B9"
    api_filter_admin_level = 2
