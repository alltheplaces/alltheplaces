from locations.spiders.mcdonalds_cz import McdonaldsCZSpider


class McdonaldsSKSpider(McdonaldsCZSpider):
    name = "mcdonalds_sk"
    allowed_domains = ["www.mcdonalds.sk"]
    start_urls = [
        "https://restauracie.mcdonalds.sk/api?token=7983978c4175e5a88b9a58e5b5c6d105217fbc625b6c20e9a8eef3b8acc6204f"
    ]
