from locations.spiders.valero import ValeroSpider


class TexacoGBIESpider(ValeroSpider):
    name = "texaco_gb_ie"
    item_attributes = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    allowed_domains = ["valero.com"]

    usa_bbox = [-10, 49, 2, 61]
