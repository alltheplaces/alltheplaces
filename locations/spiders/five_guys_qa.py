from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysQASpider(FiveGuysAUSpider):
    name = "five_guys_qa"
    experience_key = "search-backend-qa"
    locale = "ar-QA"

    def process_websites(self, item) -> None:
        item["extras"]["website:ar"] = item["website"]
        item["extras"]["website:en"] = item["website"].replace("fiveguys.qa/", "fiveguys.qa/en_qa/")
