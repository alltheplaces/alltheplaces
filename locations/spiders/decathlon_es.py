from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonESSpider(DecathlonFRSpider):
    name = "decathlon_es"
    key = "woos-5dbb4402-9d17-366b-af49-614910204d64"
    origin = "https://www.decathlon.es"
    website_template = "https://www.decathlon.es/es/store-view/tienda-de-deportes-{slug}-{ref}"
