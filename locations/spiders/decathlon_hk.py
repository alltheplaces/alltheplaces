from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonHKSpider(DecathlonFRSpider):
    name = "decathlon_hk"
    key = "woos-728dcea4-4a6f-322a-8a84-0bb40fe79c59"
    origin = "https://www.decathlon.com.hk"
    website_template = "https://www.decathlon.com.hk/en/store-view/sport-shop-{slug}-{ref}"
