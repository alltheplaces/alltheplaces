from locations.storefinders.mcdonalds_premier_capital import McdonaldsPremierCapitalSpider


class McdonaldsGRSpider(McdonaldsPremierCapitalSpider):
    name = "mcdonalds_gr"
    domain = "mcdonalds.gr"
    start_urls = ["https://mcdonalds.gr/en/locate/"]
