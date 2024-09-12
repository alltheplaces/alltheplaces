from locations.storefinders.rio_seo import RioSeoSpider


class CheckNGoUSSpider(RioSeoSpider):
    name = "check_n_go_us"
    item_attributes = {
        "brand_wikidata": "Q96067540",
        "brand": "Check 'n Go",
    }
    end_point = "https://maps.locations.checkngo.com"
