from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysNLSpider(FiveGuysAUSpider):
    name = "five_guys_nl"
    experience_key = "search-backend-nl"
    locale = (
        "en-NL"  # Using en because it has google attributes which gives lots of extra details (not present in nl-NL)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:nl"] = item["website"].replace("/en_nl/", "/")
        item["website"] = item["extras"]["website:nl"]
