# TekBetter - Data scraper

This is the data scraper which scrapes the data from the Epitech intranet and MyEpitech to sent it to the TekBetter API.

## How it works
You provide your microsoft auth cookies, and the scraper will use them to authenticate and scrape the data from the intranet and MyEpitech.

There are two available modes:
- `Private mode`: You provide your own cookies in a configuration file, and the scraper will only scrape your data. It's recommended to secure your cookies by using a personal scraper.
- `Public mode`: The TekBetter server has a list of cookies, and accounts will be shared between all scrapers. This is only used for user who can't use a personal scraper.

After scraping the data, the scraper will send it to the TekBetter API.

## Used data
The scraper will scrape the following data:
* From the `intra.epitech.eu`:
  * Your first/last name
  * Your Epitech campus name
  * All available projects, modules and activities
  * Your calendar
  * Other users photos
  * Your grades and GPA
  * Your credits
* From the `my.epitech.eu` (api.epitest.eu):
  * All your projects tests results ("Moulinettes")

## Environment variables

The following environment variables are required:

- `TEKBETTER_API_URL`: The URL of the TekBetter API
- `TEKBETTER_API_TOKEN`: The token to authenticate to the TekBetter API, only for the `Public mode`
- `SCRAPER_MODE`: The mode of the scraper, either `private` or `public`
- `SCRAPER_CONFIG_FILE`: The path to the configuration file, only for the `Private mode`