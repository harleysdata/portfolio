# Halloween Weekend Picker: group planning for a Discord server

**Type:** community tool I designed, built and ran for a real event season.
**Tools:** Google Apps Script · Google Sheets (votes and live formulas) · HTML, CSS and plain JavaScript.
**Who it's for:** a Discord server with about 1,200 members in the Toronto area, planning Halloween 2026 outings.

---

## The problem

Every October the same thing happens in a big server: dozens of people want to "do something for Halloween", the ideas scatter across several channels, and the plan that wins is whatever got posted last. Polls in Discord only handle one question at a time, and they can't answer the questions that actually decide a plan:

- Which **day** are most people free, and daytime or evening?
- How **far** are people willing to go: downtown, the GTA, or a day trip?
- Do people want a **scream park, a haunted trail, a party** or something low-key?
- Of the 70+ events running that weekend, which ones do enough people want to make a group?

## What I built

Two pages, one link each, shared in the server. No sign-up: you type a name and start tapping.

### 1. Weekend Picker (Fri Oct 16 – Sun Oct 18)

| Part | What it does |
|---|---|
| **Vote by day** | For each day: when you're free, which areas you'd go to, what kind of event you feel like, and up to 3 hearted events |
| **Live group results** | Who's free, bar charts for areas and event types, most-hearted events, and a one-line verdict in the form *"Most want Downtown Toronto and scream parks. Best time: evening."* |
| **Event list** | 77 curated Ontario events, colour-coded (ends this weekend, scream park, 19+ party, escape room), sorted by distance from Union Station, with a *Match the group's top picks* filter |

### 2. Night Picker (Devil's Night Oct 30 + Halloween Oct 31)

A second page for the two biggest nights of the season.

| Part | What it does |
|---|---|
| **Yes / Maybe / No per night** | Then time slot (early evening to after hours), area and vibe |
| **Vibe tags** | Goth, alt, mainstream and confirmed queer-friendly, so the list fits the people actually in the server. Your vibes move to the top. |
| **"I'm in" on events** | 34 events across both nights, including our own server party, with the names of who's going next to each one |

### For the organisers

Votes land in a Google Sheet. A **Summary** tab built from `COUNTIF` formulas totals everything automatically, so organisers could read the result straight from the sheet without opening the app.

## Design decisions

| Decision | Why |
|---|---|
| **No accounts** | A Discord crowd won't create a login for a poll. Each device gets a random key, so you can come back and change your vote, but nobody else can. |
| **Auto-save** | People vote on their phones between other things. Picks save 1.5 seconds after you stop tapping, and the night page also saves when you leave the tab. |
| **Results visible to everyone** | Seeing how many people are free Saturday evening is what gets the next person to vote and commit. |
| **One verdict line** | Most people won't read charts. A sentence like "Leading: Goth Zombie Prom" does the coordinating for you. |
| **Curated, not scraped** | I built the event list by hand from public Halloween listings, leaving out ghost walks and anything without a clear date. Every event links to its source so people can check times before buying. |
| **Safe by default** | Inputs are limited to known options, text is trimmed and stripped of characters that could run as spreadsheet formulas, and a lock stops simultaneous votes overwriting each other. The party's address stayed in Discord, not on the page. |

## What's here

| File | What it is |
|---|---|
| [`app/Code.gs`](app/Code.gs) | Server side: both pages, saving and reading votes, building the Summary tabs |
| [`app/Index.html`](app/Index.html) | Weekend Picker page |
| [`app/Night.html`](app/Night.html) | Night Picker page |

The event lists are trimmed to three examples per page, and the Night Picker's decorative animated theme is left out. The logic is unchanged.

## Run your own copy

1. Create a Google Sheet and copy its ID from the URL into `SHEET_ID` in `Code.gs`.
2. In **Extensions → Apps Script**, add `Code.gs` and HTML files named `Index` and `Night`.
3. **Deploy → New deployment → Web app**, Execute as: *Me*, Who has access: *Anyone*.
4. Share `/exec` for the weekend page and `/exec?p=night` for the night page. The sheet tabs are created on first visit.

## Honest limits

- **Names are self-reported.** Anyone with the link could vote as anyone. For a friendly server that was fine; for anything with stakes it wouldn't be.
- **The event list was a snapshot.** I checked listings on Oct 10 and Oct 15, and prices and times can change after that, which is why every event links to its source.
- **It was built for one season.** The dates and events are hard-coded. Making it reusable would mean moving events into the sheet and adding an admin page, which is roughly what I did next in [Project 6](../06-gta-womens-circle/).
