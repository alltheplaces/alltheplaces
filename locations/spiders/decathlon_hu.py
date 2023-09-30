from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonHUSpider(DecathlonFRSpider):
    name = "decathlon_hu"
    key = "woos-f4e1c407-8623-32f6-aaf9-c586e8ef2337"
    origin = "https://www.decathlon.hu"
    website_template = "https://www.decathlon.hu/store-view/sportaruhaz-{slug}-{ref}"
