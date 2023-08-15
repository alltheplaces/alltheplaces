from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonNLSpider(DecathlonFRSpider):
    name = "decathlon_nl"
    key = "woos-3019bc60-8e57-3c2a-8e6f-1893e1e44466"
    origin = "https://www.decathlon.nl"
    website_template = "https://www.decathlon.nl/store-view/sportwinkel-{slug}-{ref}"
