from locations.spiders.valero import ValeroSpider


class ValeroGBIESpider(ValeroSpider):
    name = "valero_gb_ie"
    item_attributes = {"brand": "Valero", "brand_wikidata": "Q1283291"}
    allowed_domains = ["valero.com"]

    usa_bbox = [-10, 49, 2, 61]
    xstep=20
    ystep=20
