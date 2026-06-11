from locations.storefinders.mcdonalds_premier_capital import McdonaldsPremierCapitalSpider


class McdonaldsEESpider(McdonaldsPremierCapitalSpider):
    name = "mcdonalds_ee"
    domain = "mcdonalds.ee"
    start_urls = ["https://mcdonalds.ee/positsioneeri/"]
