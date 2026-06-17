from locations.spiders.valero import ValeroSpider


class TexacoGBIESpider(ValeroSpider):
    name = "texaco_gb_ie"
    item_attributes = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    usa_bbox = [-10, 49, 2, 61]
    xstep = 5
    ystep = 5
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {"referer": "https://locations.valero.com/?site=UK"},
    }
