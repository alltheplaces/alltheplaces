from locations.spiders.valero import ValeroSpider

uusa_bbox = [-10, 49, 2, 61]

xstep = 5
ystep = 3


class TexacoGBIESpider(ValeroSpider):
    name = "texaco_gb_ie"
    item_attributes = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    allowed_domains = ["valero.com"]
