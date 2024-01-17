from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonTRSpider(DecathlonFRSpider):
    name = "decathlon_tr"
    key = "woos-02fa0b82-a54d-3cc3-bdfa-3ce69249f220"
    origin = "https://www.decathlon.com.tr"
    website_template = "https://www.decathlon.com.tr/store-view/magaza-spor-{slug}-{ref}"
