# YouTube Dislike Count in Bulk: API to CSV Export

[![YouTube Scraper on Apify][badge-yt]][store-yt]

Export the **YouTube dislike count in bulk** for a list of videos or a whole channel, together with views, likes and the like/dislike ratio. This repo is a small Node.js and Python tool around a hosted **YouTube dislike count API**: the [YouTube Scraper][store-yt] Actor on Apify, which adds an estimated dislike count from [Return YouTube Dislike](https://returnyoutubedislike.com) to every video row. You don't need a YouTube API key, a Google Cloud project or a login.

> **Dislikes are estimates.** YouTube hid public dislike counts in November 2021. The numbers here come from the community [Return YouTube Dislike](https://returnyoutubedislike.com) project, not from YouTube.

## What you get

One CSV row per video. This is real output from a test run on 2026-09-26 ([`samples/videos-sample.csv`](samples/videos-sample.csv)):

| Title | Channel | Views | Likes | Dislikes (est.) | Likes per dislike | Like % |
|---|---|---:|---:|---:|---:|---:|
| Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster) | Rick Astley | 1,820,175,989 | 19,421,633 | 519,439 | 37.4 | 97.4% |
| Me at the zoo | jawed | 436,897,923 | 19,931,881 | 447,748 | 44.5 | 97.8% |
| Justin Bieber - Baby ft. Ludacris | Justin Bieber | 3,758,230,585 | 28,806,960 | 17,847,189 | 1.6 | 61.7% |
| PSY - GANGNAM STYLE(강남스타일) M/V | officialpsy | 6,073,749,209 | 32,253,534 | 4,000,675 | 8.1 | 89.0% |

And the 5 newest videos of a channel ([`samples/channel-sample.csv`](samples/channel-sample.csv), `--channel @veritasium --max 5`):

| Title | Views | Likes | Dislikes (est.) | Likes per dislike | Like % |
|---|---:|---:|---:|---:|---:|
| We sent a camera to space to film the solar eclipse | 2,687,119 | 67,085 | 1,113 | 60.3 | 98.4% |
| The Scariest Chart in Electrical Engineering | 5,857,462 | 147,971 | 2,248 | 65.8 | 98.5% |
| Why does every mammal get 1 billion heartbeats in their life? | 6,416,274 | 151,683 | 2,020 | 75.1 | 98.7% |
| The Insane Real Engineering of the Nazi Enigma Machine | 7,373,043 | 82,311 | 965 | 85.3 | 98.8% |
| Is spider web really stronger than steel? | 9,220,451 | 141,315 | 1,849 | 76.4 | 98.7% |

CSV columns:

| Column | Meaning |
|---|---|
| `video_id`, `title`, `url`, `channel` | The video |
| `published_at` | Upload date (`YYYY-MM-DD`) |
| `views`, `likes` | Public view and like counts at the time of the run |
| `dislikes_estimated` | Return YouTube Dislike estimate |
| `like_dislike_ratio` | `likes / dislikes` (37.4 = 37.4 likes for every dislike) |
| `like_percent` | `likes / (likes + dislikes) × 100` |
| `ryd_rating` | Return YouTube Dislike's 1-5 rating for the video |

The full row the Actor returns (description, hashtags, description links, subscriber count and more) is in [`samples/raw-row.json`](samples/raw-row.json).

## Quick start

1. Create a free Apify account and copy your API token ([sign up][signup], then Console > Settings > API & Integrations).
2. `cp .env.example .env` and paste the token after `APIFY_TOKEN=`.

**Node.js** (20.6 or newer):

```bash
npm install
node --env-file=.env dislikes.mjs "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "https://youtu.be/kffacxfA7G4"
node --env-file=.env dislikes.mjs --file videos.example.txt --out my-videos.csv
node --env-file=.env dislikes.mjs --channel @veritasium --max 50 --out veritasium.csv
```

**Python** (3.10 or newer):

```bash
pip install -r requirements.txt
python dislikes.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
python dislikes.py --file videos.example.txt --out my-videos.csv
python dislikes.py --channel @veritasium --max 50 --out veritasium.csv
```

Options (both scripts):

| Option | What it does | Default |
|---|---|---|
| video URLs | Any mix of `watch?v=`, `youtu.be/`, `/shorts/` and `/embed/` links, or bare 11-character IDs | |
| `--file videos.txt` | One video per line; lines starting with `#` are skipped | |
| `--channel <name>` | A channel name, `@handle` or channel URL. Repeat it for several channels | |
| `--max N` | How many videos per channel, newest first | `20` |
| `--out file.csv` | Where to write the CSV | `dislikes.csv` |
| `--max-charge USD` | Hard cost cap for the run, enforced by Apify | `1` |

## Use it as a YouTube dislike count API (curl)

No script needed. One HTTP call starts the Actor, waits for it and returns the rows as CSV or JSON:

```bash
curl -s -X POST \
  "https://api.apify.com/v2/acts/yugenox~youtube-scraper/run-sync-get-dataset-items?format=csv&fields=id,title,viewCount,likes,dislikes,rating" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"startUrls":["https://www.youtube.com/watch?v=dQw4w9WgXcQ","https://www.youtube.com/watch?v=kffacxfA7G4"],"includeDislikes":true}'
```

```csv
"id","title","viewCount","likes","dislikes","rating"
"kffacxfA7G4","Justin Bieber - Baby ft. Ludacris","3758234070","28806968","17847189","3.4696679646812334"
"dQw4w9WgXcQ","Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)","1820175989","19421636","519439","4.895758513849566"
```

Use `format=json` for JSON, or `format=xlsx` for Excel. The synchronous endpoint waits up to 5 minutes; for big lists, start a normal run and read its dataset afterwards (that is what the scripts do). Other ways to call it (Python and JS clients, OpenAPI, MCP for AI agents) are on the Actor's [API page][api-yt].

## How the numbers are produced

- **Views and likes** are read from YouTube's public video data when the run happens. Likes are empty when a creator hides them.
- **Dislikes** come from the [Return YouTube Dislike](https://returnyoutubedislike.com) API. For videos from before late 2021 the count is largely based on archived real dislike data. Newer numbers are extrapolated from the votes of people who use the Return YouTube Dislike browser extension, so treat them as estimates. Rows carry `dislikesEstimated: true` in the raw output.
- **Ratios** are computed by the script from those two numbers.

## Why this instead of the YouTube Data API

The official [YouTube Data API v3](https://developers.google.com/youtube/v3) is the right tool for your own channel's analytics and for anything that must be official Google data. For dislike counts in bulk it doesn't help:

- **No public dislike counts.** Since December 13, 2021 `statistics.dislikeCount` is only returned to the video's owner, not for other people's videos.
- **Daily quota.** Projects get 10,000 quota units a day by default. `videos.list` costs 1 unit, but `search.list` costs 100 units, which is about 100 searches a day.
- **Setup.** You need a Google Cloud project and an API key. Here you need one Apify token.

**Why not call Return YouTube Dislike yourself?** For a handful of videos you should: it is free. Their API allows 100 requests a minute and 10,000 a day per client, and returns counts only (no title, channel or upload date). This repo is for when you want the counts joined with each video's metadata, for a whole channel or a list of thousands of videos, in one CSV.

## Price

Pay per result, no subscription. Prices checked on 2026-10-06 from the Apify API:

| Option | Dislikes | Price per 1,000 videos |
|---|---|---|
| **[yugenox/youtube-scraper][store-yt]** (this repo) | Estimated (Return YouTube Dislike), in the same row as views, likes and metadata | **$2.00**, dislikes and comments included |
| streamers/youtube-scraper, Apify Free plan price | Not offered | $4.00 |
| YouTube Data API v3 | Not returned for other people's videos | Free within quota |
| Return YouTube Dislike API directly | Counts only | Free, rate-limited |

Examples at $2.00 per 1,000: 100 videos cost $0.20, a 500-video channel costs $1.00. Each run also has a start fee of $0.00005 per GB of memory. Apify's free plan includes monthly credit you can spend on this, and `--max-charge` caps any single run.

## Limits

- Estimates can be far off for small or very new videos with few extension users.
- Some videos have no Return YouTube Dislike data yet; `dislikes_estimated` is then empty.
- Private or removed videos and channels that don't exist return no row and aren't charged; the run lists them in its `ERRORS` record (Apify Console > Storage > Key-value store) and in its status message.
- Public videos only. Nothing here signs in to YouTube.

## More

- Every input mode of the YouTube and Instagram scrapers in Node, Python, curl, Apify CLI and Google Sheets: [youtube-instagram-scraper-examples](https://github.com/ArpitGandhi1934/youtube-instagram-scraper-examples)
- Instagram Reels to text in bulk: [instagram-reels-transcript-bulk](https://github.com/ArpitGandhi1934/instagram-reels-transcript-bulk)
- Instagram comments to Excel or CSV: [instagram-comments-export](https://github.com/ArpitGandhi1934/instagram-comments-export), which calls the [Instagram Comments Scraper][store-igc]
- Use the YouTube Scraper from Claude, ChatGPT, Cursor or VS Code through a pinned Apify MCP server: [yugenox-mcp](https://github.com/ArpitGandhi1934/yugenox-mcp)
- Guides on [yugenox-data.vercel.app](https://yugenox-data.vercel.app): [YouTube dislike count API](https://yugenox-data.vercel.app/youtube/dislike-count-api), [YouTube Data API alternative without quota](https://yugenox-data.vercel.app/youtube/data-api-alternative), [pricing calculator](https://yugenox-data.vercel.app/pricing-calculator)
- The Actor itself, with its input form, output schema and reviews: [YouTube Scraper on Apify][store-yt]

## Credits and legal

- Dislike data: [Return YouTube Dislike](https://returnyoutubedislike.com) ([source code](https://github.com/Anarios/return-youtube-dislike)). Their API terms ask third-party users to credit the project with a link, as above.
- Not affiliated with YouTube or Google. YouTube is a trademark of Google LLC.
- The Actor collects publicly available data only. Channel names are personal data in some jurisdictions; follow GDPR, PIPEDA, CCPA and YouTube's terms when you store or publish results. See [Is web scraping legal?][legal].
- Input keys verified against the Actor's input schema on 2026-09-26 (build 0.1.11) and again on 2026-10-06 (build 0.1.14).
- MIT licensed. Made by Yugenox Corporation.

<!-- All apify.com links for this README live below. When the Apify affiliate id exists, append ?fpr=<id> to these URLs only. -->
[store-yt]: https://apify.com/yugenox/youtube-scraper
[api-yt]: https://apify.com/yugenox/youtube-scraper/api
[store-igc]: https://apify.com/yugenox/instagram-comments-scraper
[badge-yt]: https://apify.com/actor-badge?actor=yugenox/youtube-scraper
[signup]: https://console.apify.com/sign-up
[legal]: https://blog.apify.com/is-web-scraping-legal/
