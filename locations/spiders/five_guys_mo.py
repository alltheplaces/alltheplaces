from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysMOSpider(FiveGuysAUSpider):
    name = "five_guys_mo"
    experience_key = "search-backend-mo"
    locale = "en-MO"  # Using en because it has google attributes which gives lots of extra details (not present in zh-Hant-MO)

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:zh"] = item["website"].replace("/en/", "/").replace("/en_mo/", "/")
        item["website"] = item["extras"]["website:zh"]
