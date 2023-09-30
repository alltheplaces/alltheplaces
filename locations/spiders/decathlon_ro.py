from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonROSpider(DecathlonFRSpider):
    name = "decathlon_ro"
    key = "woos-a11e8e0e-80e2-35e1-8316-ca1d015a4ed0"
    origin = "https://www.decathlon.ro"
    website_template = "https://www.decathlon.ro/store-view/magazin-sport-{slug}-{ref}"
