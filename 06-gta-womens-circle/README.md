# GTA Women's Circle: member matching and events app

**Type:** community tool I designed, built and run as admin.
**Tools:** Google Apps Script · Google Sheets (as the database) · HTML, CSS and plain JavaScript · no paid services.
**Who it's for:** a women's group chat on Instagram with about 1,000 members across Toronto and the GTA.

---

## The problem

A big group chat is good at one thing: everyone sees everything. That makes it bad at the thing members actually joined for, which is finding a few people nearby who want to do the same things and making a real plan.

- "Anyone want to go to X?" messages get buried within an hour.
- Nobody knows who else lives near them or likes pottery, hiking or concerts.
- Members can't easily share their Instagram with *some* people without posting it to all 1,000.
- As the admin, I had no structured way to see what the group wanted or to keep out people who weren't part of it.

## What I built

A small web app that sits alongside the chat. Members open one link; there's nothing to install and no account to create.

| Part | What it does |
|---|---|
| **Profile** | Nickname, general area, the hobbies they want to make plans around, the kinds of events they want to try, when they're usually free and their budget. Instagram is optional and only shown if they choose. |
| **Matches** | Ranks other members by shared hobbies, shared event types, same area, overlapping free time and budget. "Interest circles" show how many members share each hobby and how many are nearby. |
| **Events** | Free and paid events across the GTA, filterable by type, price and area. Members tap *Interested* or *Going* and see who else is in, so a match turns into an actual plan. |
| **Suggest an event** | Any member can submit an event; it goes live after admin approval. |
| **Admin** | I approve new members (checking they're in the chat), approve or reject event suggestions, review private reports, and remove members. |

### How matching works

```
score = 2 × shared hobbies
      + 1 × shared event types
      + 3 if same area
      + 1 if free at overlapping times
      + 1 if budgets are compatible
```

Hobbies count double because they're the strongest signal that two people will actually enjoy a plan together. Area gets a flat bonus because in the GTA, a 90-minute transit trip kills most plans.

## Designing for a real group, not a demo

The technical side is small on purpose. Most of the decisions were about the people using it.

| Decision | Why |
|---|---|
| **Invite code + admin approval** | The group is women-only and safety matters more than growth. A shared code keeps out strangers who find the link; approval lets me check each person is actually in the chat. |
| **Collect as little as possible** | No last name, phone, address, birthday or photos. Location is a general area plus, optionally, the first 3 characters of a postal code (for example `L5B`), never the full code. |
| **Instagram is opt-in** | It's the main way members connect, but it's also the most personal thing on a profile. If a member doesn't tick "show my Instagram", the handle isn't even saved. |
| **Pause and delete** | Members can hide themselves from matches without leaving, or delete their profile and RSVPs in one step. |
| **Private reporting** | Every match card has a Report button that goes only to the admin. Removed members have their details wiped from the sheet. |
| **Safety prompts on events** | A standing reminder to meet in public, go as a group the first time, and tell a friend where you'll be. |
| **No accounts** | A login wall would lose most of a 1,000-person chat. Each device gets a random token instead (only a hash is stored), with a recovery code for using a second phone. |
| **Google Sheets as the database** | I can see, back up and export everything without a dashboard, and a co-admin can help without learning a new tool. |

## Data model

Five tabs in one Google Sheet:

| Tab | Holds |
|---|---|
| `Members` | Profile fields, status (pending / approved / removed), hashed device token |
| `Events` | Approved events: title, dates, venue, area, type, free or paid, link, notes |
| `Submissions` | Member-suggested events waiting for approval |
| `RSVPs` | Member ↔ event, *interested* or *going* |
| `Reports` | Private reports, with a resolved flag |

## What's here

| File | What it is |
|---|---|
| [`app/Code.gs`](app/Code.gs) | Server side: setup, member and admin API, validation, locking |
| [`app/Index.html`](app/Index.html) | The whole front end: profile, matches, events, admin |

## Run your own copy

1. Create a Google Sheet, then open **Extensions → Apps Script**.
2. Paste `Code.gs`, and add an HTML file named `Index` with `Index.html`.
3. Run `setup` once and approve the permissions. The log shows your join code and admin key.
4. **Deploy → New deployment → Web app**, Execute as: *Me*, Who has access: *Anyone*.
5. Change `JOIN_CODE` under **Project Settings → Script properties** before sharing the link.

The admin view is the same link with `?admin=1` added.

## Honest limits

- **It's new.** I launched it in November 2026, so I don't have usage numbers yet. The things I plan to track are sign-ups and approval rate, the share of members with at least one match in their area, and how many events get two or more RSVPs from members.
- **Sheets is not a real database.** Every request reads whole tabs. That's fine for a few hundred active members, and I'd move to Supabase (Postgres with row-level security) if it grows past that.
- **The device token is convenience, not security.** Anyone with a member's recovery code can edit that profile. That's an acceptable trade-off for nicknames and hobby tags; it wouldn't be for anything more sensitive.
- **Events are curated by hand.** Most event sites don't offer free feeds, so the list relies on me and member suggestions. A weekly "add five events" routine keeps it fresh.
- **Matching is a simple weighted score.** It's easy to explain to members, which matters more right now than squeezing out better ranking.

## What I'd add next

- A weekly digest posted in the chat: new events, and new members near you.
- Small "plans": a member proposes a hangout, up to six others join.
- Event feeds from sources that offer them (City of Toronto open data, library calendars) so I curate less by hand.
