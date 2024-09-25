from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysCNSpider(FiveGuysAUSpider):
    name = "five_guys_cn"
    experience_key = "search-backend-cn"
    locale = (
        "en-CN"  # Using en because it has google attributes which gives lots of extra details (not present in zh-Hans)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"].replace("fiveguys.cn/", "fiveguys.cn/en_cn/")
        item["extras"]["website:zh"] = item["website"]
