from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonCHSpider(DecathlonFRSpider):
    name = "decathlon_ch"
    key = "woos-7b40f2ea-b0a6-3a3b-9315-53ca807b601c"
    origin = "https://www.decathlon.ch"
    website_template = "https://www.decathlon.ch/de/store-view/filiale-{slug}-{ref}"
