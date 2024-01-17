from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonGBSpider(DecathlonFRSpider):
    name = "decathlon_gb"
    key = "woos-4c9860ae-4147-39e0-af88-6d56fc1a5ab6"
    origin = "https://www.decathlon.co.uk"
    website_template = "https://www.decathlon.co.uk/store-view/sport-shop-{slug}-{ref}"
