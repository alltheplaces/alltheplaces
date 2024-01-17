from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonCZSpider(DecathlonFRSpider):
    name = "decathlon_cz"
    key = "woos-8e13088e-16a2-322a-9440-1681be0d34ef"
    origin = "https://www.decathlon.cz"
    website_template = "https://www.decathlon.cz/store-view/sportovni-prodejna-{slug}-{ref}"
