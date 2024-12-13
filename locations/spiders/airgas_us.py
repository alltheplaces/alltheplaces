from locations.storefinders.rio_seo import RioSeoSpider


class AirgasUSSpider(RioSeoSpider):
    name = "airgas_us"
    item_attributes = {"brand": "Airgas", "brand_wikidata": "Q80635"}
    end_point = "https://maps.locations.airgas.com"
