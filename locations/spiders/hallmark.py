from locations.storefinders.rio_seo import RioSeoSpider


class HallmarkSpider(RioSeoSpider):
    name = "hallmark"
    item_attributes = {"brand": "Hallmark", "brand_wikidata": "Q1521910"}
    end_point = "https://maps.hallmark.com"
