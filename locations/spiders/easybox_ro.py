from locations.spiders.easybox_bg import EasyboxBGSpider


class EasyboxROSpider(EasyboxBGSpider):
    name = "easybox_ro"
    allowed_domains = ["sameday.ro"]
    start_urls = ["https://sameday.ro/wp/wp-admin/admin-ajax.php?action=get_ooh_lockers_request&country=Romania"]
