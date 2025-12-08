from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysITSpider(FiveGuysAUSpider):
    name = "five_guys_it"
    experience_key = "search-backend-it"
    locale = (
        "en-IT"  # Using en because it has google attributes which gives lots of extra details (not present in it-IT)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:it"] = item["website"].replace("/en_it/", "/")
        item["website"] = item["extras"]["website:it"]
