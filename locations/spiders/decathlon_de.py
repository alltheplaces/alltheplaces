from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonDESpider(DecathlonFRSpider):
    name = "decathlon_de"
    key = "woos-77d134ba-bbcc-308d-959e-9a8ce014dfec"
    origin = "https://www.decathlon.de"
    website_template = "https://www.decathlon.de/store-view/filiale-{slug}-{ref}"
