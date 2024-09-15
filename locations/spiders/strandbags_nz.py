from locations.spiders.strandbags_au import StrandbagsAUSpider


class StandbagsNZSpider(StrandbagsAUSpider):
    name = "strandbags_nz"
    key = "u9317"
    drop_attributes = {"state"}
