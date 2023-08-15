from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonITSpider(DecathlonFRSpider):
    name = "decathlon_it"
    key = "woos-25d7be73-ee80-3e98-915d-a5349756f5d2"
    origin = "https://www.decathlon.it"
    website_template = "https://www.decathlon.it/store-view/negozio-sport-{slug}-{ref}"
