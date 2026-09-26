#!/usr/bin/env node
// YouTube dislike count in bulk -> CSV.
//
// Calls the yugenox/youtube-scraper Actor on Apify with includeDislikes on, then writes one CSV
// row per video: views, likes, estimated dislikes (Return YouTube Dislike) and like/dislike ratio.
//
// Usage:
//   node --env-file=.env dislikes.mjs <video-url> [<video-url> ...]
//   node --env-file=.env dislikes.mjs --file videos.txt
//   node --env-file=.env dislikes.mjs --channel @veritasium --max 25
//   ...add --out my.csv to choose the output file (default: dislikes.csv)
//
// Requires Node 20.6+ and APIFY_TOKEN in the environment (or in .env).

import { writeFileSync, readFileSync } from 'node:fs';
import { ApifyClient } from 'apify-client';

const ACTOR = 'yugenox/youtube-scraper';

function parseArgs(argv) {
    const opts = { urls: [], channels: [], max: 20, out: 'dislikes.csv', maxCharge: 1 };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--file') {
            const lines = readFileSync(argv[++i], 'utf8').split('\n').map((s) => s.trim());
            opts.urls.push(...lines.filter((s) => s && !s.startsWith('#')));
        } else if (a === '--channel') opts.channels.push(argv[++i]);
        else if (a === '--max') opts.max = Number(argv[++i]);
        else if (a === '--out') opts.out = argv[++i];
        else if (a === '--max-charge') opts.maxCharge = Number(argv[++i]);
        else if (a.startsWith('--')) throw new Error(`Unknown option ${a}`);
        else opts.urls.push(a);
    }
    if (!opts.urls.length && !opts.channels.length) {
        throw new Error('Give at least one video URL, --file videos.txt, or --channel @handle');
    }
    return opts;
}

// likes / dislikes, e.g. 37.4 means 37.4 likes for every dislike
function ratio(likes, dislikes) {
    if (likes == null || dislikes == null) return '';
    if (dislikes === 0) return '';
    return (likes / dislikes).toFixed(1);
}

// share of likes among all votes, in percent
function likePercent(likes, dislikes) {
    if (likes == null || dislikes == null || likes + dislikes === 0) return '';
    return ((likes / (likes + dislikes)) * 100).toFixed(1);
}

function csvCell(v) {
    if (v == null) return '';
    const s = String(v);
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

const COLUMNS = [
    'video_id', 'title', 'url', 'channel', 'published_at', 'views', 'likes',
    'dislikes_estimated', 'like_dislike_ratio', 'like_percent', 'ryd_rating',
];

function toRow(v) {
    const dislikes = typeof v.dislikes === 'number' ? v.dislikes : null;
    const likes = typeof v.likes === 'number' ? v.likes : null;
    return {
        video_id: v.id,
        title: v.title,
        url: v.url,
        channel: v.channelName,
        published_at: v.publishedAt ?? v.date,
        views: v.viewCount,
        likes,
        dislikes_estimated: dislikes,
        like_dislike_ratio: ratio(likes, dislikes),
        like_percent: likePercent(likes, dislikes),
        ryd_rating: typeof v.rating === 'number' ? v.rating.toFixed(2) : '',
    };
}

async function main() {
    const opts = parseArgs(process.argv.slice(2));
    if (!process.env.APIFY_TOKEN) throw new Error('Set APIFY_TOKEN (see .env.example)');

    const input = { includeDislikes: true, maxItems: opts.max };
    if (opts.urls.length) input.startUrls = opts.urls;
    if (opts.channels.length) input.channels = opts.channels;

    const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
    console.error(`Running ${ACTOR} ...`);
    // maxTotalChargeUsd caps what this run can cost you (pay-per-event Actors only).
    const run = await client.actor(ACTOR).call(input, { maxTotalChargeUsd: opts.maxCharge });
    console.error(`Run ${run.id} finished: ${run.status}`);

    const { items } = await client.dataset(run.defaultDatasetId).listItems();
    const videos = items.filter((it) => !it.error);
    const errors = items.filter((it) => it.error);
    for (const e of errors) console.error(`skipped ${e.input || e.url || e.id}: ${e.error}`);

    const lines = [COLUMNS.join(',')];
    for (const v of videos) {
        const row = toRow(v);
        lines.push(COLUMNS.map((c) => csvCell(row[c])).join(','));
    }
    writeFileSync(opts.out, `${lines.join('\n')}\n`);
    console.error(`Wrote ${videos.length} videos to ${opts.out}`);
    console.error('Dislike counts are estimates from Return YouTube Dislike (returnyoutubedislike.com).');
}

main().catch((err) => {
    console.error(err.message);
    process.exit(1);
});
