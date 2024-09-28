from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysSASpider(FiveGuysAUSpider):
    name = "five_guys_sa"
    experience_key = "search-backend-sa"
    locale = "ar-SA"

    def process_websites(self, item) -> None:
        item["extras"]["website:ar"] = item["website"]
        item["extras"]["website:en"] = item["website"].replace("fiveguys.sa/", "fiveguys.sa/en_sa/")
