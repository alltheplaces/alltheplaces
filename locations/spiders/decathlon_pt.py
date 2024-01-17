from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonPTSpider(DecathlonFRSpider):
    name = "decathlon_pt"
    key = "woos-c224dd3f-84cf-336c-a5f8-ef7272389ae3"
    origin = "https://www.decathlon.pt"
    website_template = "https://www.decathlon.pt/store-view/loja-de-desporto-{slug}-{ref}"
