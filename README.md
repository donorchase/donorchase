# DonorChase website

Static copy of donorchase.com, rebuilt for GitHub Pages, with the homepage repositioned
around **"Track what's owed. Chase it. See it reconcile in Xero."** and three new segment
landing pages.

## What's in here

| Path | What it is |
|---|---|
| `src/pages/` | One file per page. Edit these to change the site. |
| `src/static/css/site.css` | All styling (same design as the live site). |
| `src/static/js/site.js` | Mobile menu, "Who it's for" dropdown, contact form. |
| `src/static/images/` | Images (see step 3 below). |
| `build.py` | Builds the finished site into `_site/` (Python 3, no installs). |
| `.github/workflows/deploy.yml` | Rebuilds and publishes automatically on every push. |

### Pages

All existing URLs are kept, so links and Google rankings carry over:

- `/` homepage (repositioned) · `/non-profit-accounting-software` pricing · `/donation-tracking-software` about
- `/gift-aid-review` · `/software/integrations` · `/contact-us` · `/privacy-policy` · `/terms-and-conditions`
- `/help-articles` + 4 articles · `/blog-and-news` + 4 posts

New:

- `/schools` · `/membership-charities` · `/event-pledges` (also in a "Who it's for" menu and the footer)

### Links to DonorBoost

DonorBoost (https://donorboost.co.uk/) is linked from:

- the **Gift Aid** menu, which is now a dropdown: *Gift Aid reviews* and *DonorBoost*
- a new **Our products** column in the footer of every page
- a green DonorBoost panel on the homepage, the Gift Aid page, and all three segment pages,
  each worded for that audience
- the About page ("Where do we plan going next?" now says Gift Aid claims are handled by DonorBoost)
- the Gift Aid FAQs on the Schools and Event pledges pages

The contact form also asks "What are you interested in?" (DonorChase / DonorBoost / Gift Aid review),
so enquiries show which product they're about. To change the DonorBoost address, edit
`DONORBOOST_URL` at the top of `build.py`.

## Publish on GitHub Pages

1. **Create a repository** on GitHub (e.g. `donorchase-site`) and upload everything in this folder,
   including the hidden `.github` folder.
2. **Turn on Pages:** repository *Settings → Pages → Build and deployment → Source: GitHub Actions*.
   Every push to `main` now rebuilds and publishes the site. The first run takes about a minute;
   the address appears in *Settings → Pages* (e.g. `https://<account>.github.io/donorchase-site/`).
3. **Images:** the pages currently load images from the live donorchase.com, so nothing looks broken.
   Before switching the domain, copy them into the repo: run `python3 build.py --fetch-images`
   (downloads all 46 into `src/static/images/`), commit, and push. Elliott can also copy them
   from the current site's `wwwroot/images` folder.
4. **Contact form:** GitHub Pages can't process forms itself, so the form posts to Formspree.
   Create a free form at formspree.io (send notifications to info@donorchase.com), copy its ID
   (the part after `formspree.io/f/`) into `FORMSPREE_ID` at the top of `build.py`, and push.
   Until then the form tells visitors to email instead.
5. **Point donorchase.com at GitHub (when ready):** *Settings → Pages → Custom domain* →
   `donorchase.com`, then update DNS at your registrar as GitHub instructs (A records for the apex,
   CNAME for `www`). Tick *Enforce HTTPS* once the certificate is issued. Do steps 3 and 4 first.

## Editing

- Change text: edit the page in `src/pages/`. The comment block at the top sets the browser
  title, the Google description and which menu item is highlighted.
- Write links as root paths (`/contact-us`, `/images/x.jpg`). The build turns them into links
  that work both on `github.io/repo/` and on the real domain.
- Header, footer and menu are defined once in `build.py`.
- Preview locally: `python3 build.py --serve`, then open http://localhost:8000.

## Tracking sign-ups by segment

Every "Book a demo" button on a segment page links to `/contact-us?segment=schools`
(or `membership` / `events`). The contact form pre-selects the matching organisation type and
sends two hidden fields with each enquiry:

- **Segment**: `schools`, `membership`, `events` or `general`
- **SourcePage**: which button or page the visitor came from

Both appear in every Formspree submission email and can be exported from Formspree as CSV.

## Content to check before launch

The segment pages describe existing features (groups/categories, standing order tracker,
chasers assigned to team members, daily/weekly reminder emails, multiple dashboards,
nightly Xero sync). The dashboards on those pages are illustrative and labelled
"Illustrative example with sample data". Two claims worth confirming:

- **Membership:** "spot who has lapsed" relies on a custom *Lapsed* group, not a dedicated
  renewal-date or lapsed-member view.
- **Events:** "pledged against received… with a running total and collection rate for the event"
  relies on one dashboard per event and its summary statistics.
