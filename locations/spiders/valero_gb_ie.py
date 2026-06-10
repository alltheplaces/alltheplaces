from locations.spiders.valero import ValeroSpider


class ValeroGBIESpider(ValeroSpider):
    name = "valero_gb_ie"
    usa_bbox = [-10, 49, 2, 61]
    xstep = 20
    ystep = 20
