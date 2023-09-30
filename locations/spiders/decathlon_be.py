from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonBESpider(DecathlonFRSpider):
    name = "decathlon_be"
    key = "woos-9f8c8ff6-ebbf-34aa-ae1c-437fde9f85e7"
    origin = "https://www.decathlon.be"
    website_template = "https://www.decathlon.be/nl/store-view/sportwinkel-{slug}-{ref}"
