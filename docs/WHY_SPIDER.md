
## Why spider?

### Magic can only get you so far

There is a theory that with lashings of AI and ML then all the worlds problems
will be solved. Maybe. However, given we are not there yet, and we wish to build
a comprehensive set of places (POI) data then web spidering is an important part
of the toolkit. However, we will automate and make easy what we can.

To do a reasonable job of extracting place data from a website it is
necessary, in many cases, to perform simple tweaks to the results of the
[automation](./STRUCTURED_DATA.md), i.e., write a little code.
In many other cases
[little automation is possible](./HARD_WORK_SPIDER.md), meaning write even more code!

Another reason to spider is that it can be made as lightweight and directed
as possible. Hence, we can afford to run it on a reasonable cadence (this type
of data is volatile) without upsetting the site from which we get it,
and at reasonable expense.

### What to spider?

Make no mistake, we cannot write a spider for every website in the world. This
is not our intention. However, for the major brands, companies, and
operators, and especially the ones that a lot of people wish to find
and visit then it can make a lot of sense.

If we are writing tens of lines of code to generate thousands of good quality
POIs for a site then we are winning. This is possible for companies like
McDonald's, Starbucks, Exxon, Mobil, BP, Shell and many more.

Sometimes we can relax the few sites rule when considering the importance
to the company / brand in terms of number of visitors to their locations.
For example, COSTCO and IKEA would fall into this bucket. Important
public services such as hospitals, police stations, fire stations
and public toilets are worth spending the time to develop a spider
for due to their importance to the public.

A not unreasonable rule of thumb would be that if a brand or
operator  is important enough to have merited an entry in the
[name suggestion index (NSI)](https://nsi.guide/?t=brands)
then it probably also merits a spider. Of course some
brands merit an NSI entry but do not have one yet! Read their pages,
get to understand [Wikidata](./WIKIDATA.md).

### Who uses the data?

Our data is today published on a [weekly cadence](./WEEKLY_RUN.md).
We do not know everyone who uses it, nor do we wish to.
The project has a strong open data and
[OpenStreetMap](https://www.openstreetmap.org/)
influence. Not surprising given the background of many of the contributors.
With that in mind we see a number of synergies between ATP and other
open data projects. See the end of
[our Wikidata discussion page](./WIKIDATA.md) for some thoughts.

### Encourage distributed effort

Writing a spider, just like map editing, can be labour intensive.
That said it is sometimes surprising what a few people can achieve,
especially with good local (in this case country level) knowledge.
If synergistic tooling of the type we believe possible is developed
then there will be a good incentive for some more local OSM
communities to become involved.

### An incentive for companies to help

It is also not worth forgetting the companies and brands themselves. None of
them are trying to hide. A big concern for many of them will be
how they are represented on the web in search engines, maps and
their like. There are many "shoddy" representations.

The data published by this site should show them how they "look to others"
via their site metadata. If they think it is inadequate then they
can contribute themselves by either preferably tweaking what they publish
or edit the spider for their site to be more effective.

We are not scraping their sites for price comparison purposes,
personal information or similar. We publish the minimum data for the purpose
described and consider one of the most important pieces of data
we publish to be the individual site/store page URL if it exists,
or failing that, their home page.
After knowing the site details and location it is pretty
much up to the site itself to tell the rest of their story!
