from locations.spiders.easybox_bg import EasyboxBGSpider


class EasyboxHUSpider(EasyboxBGSpider):
    name = "easybox_hu"
    allowed_domains = ["sameday.hu"]
    start_urls = ["https://sameday.hu/wp/wp-admin/admin-ajax.php?action=get_ooh_lockers_request&country=Ungaria"]
