from scrapy import cmdline

spider = "bestbuy_ca"

# cmdline.execute("rm {spider}".format(spider=spider).split())
cmdline.execute("scrapy crawl {spider} -o {spider}.ndgeojson".format(spider=spider).split())
