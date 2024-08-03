from locations.storefinders.wp_go_maps import WpGoMapsSpider


class EzMartUSSpider(WpGoMapsSpider):
    name = "ez_mart_us"
    allowed_domains = [
        "blarneycastleoil.com",
    ]
