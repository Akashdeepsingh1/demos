#!/usr/bin/env python3
"""Build crm.html: Kanban board (default) + list view, popup demo/pitch viewer,
and a correction-feedback system. Static list cards are baked in as a fallback
for viewers without JavaScript; when JS runs, the Kanban board takes over.
Data: prospects.csv + state.json. Re-run after prospect data changes.
After ANY edit to the JS, run: node --check on the extracted script.
"""
import csv, json, html, os, urllib.parse, shutil
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
STAMP = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M PDT")
BASE = os.path.expanduser("~/workspace/website-business")
rows = list(csv.DictReader(open(os.path.join(BASE, "prospects.csv"))))
state = json.load(open(os.path.join(BASE, "state.json")))
demo_slug = {pid: v["slug"] for pid, v in state.items() if isinstance(v, dict) and v.get("slug")}
PREVIEW = {
    "the-pooch-patio-dallas": "https://akashdeepsingh1.github.io/demos/preview/the-pooch-patio-dallas/",
    "boston-barber-tattoo-co-boston": "https://akashdeepsingh1.github.io/demos/preview/boston-barber-tattoo-co-boston/",
    "rooter-plumbing-service-phoenix": "https://akashdeepsingh1.github.io/demos/preview/rooter-plumbing-service-phoenix/",
}
DIRECTORY = ["yelp.com","facebook.com","instagram.com","rucat.net","barberboard.az.gov",
 "chamberofcommerce.com","search.app","demandforce.com","worldorgs.com","dogdog.org",
 "booksy.com","fresha.com","thumbtack.com","angi.com","homeadvisor.com","houzz.com",
 "tripadvisor.com","yellowpages.com","yp.com","bbb.org","manta.com","mapquest.com",
 "superpages.com","citysearch.com","local.com","groupon.com","nextdoor.com"]
BUILDERS = ["business.site","godaddysites.com","wixsite.com","weebly.com","jimdosite.com",
 "dudaone.com","strikingly.com","webnode.com","site123.me"]
TYPE_LABEL = {"none": "No website", "listing": "Listing page - not their own site",
              "builder": "Simple builder site", "own": "Own website"}
SOCIALS = {
 "355781046755374": {"fb": "https://www.facebook.com/229864424109692", "ig": "https://www.instagram.com/explore/locations/229864424109692", "yp": "https://www.yelp.com/biz/3qzjxLwpZ0_2-XrDDZzAPA"},
 "461882028922156": {"fb": "https://www.facebook.com/113394812049682", "ig": "https://www.instagram.com/explore/locations/113394812049682", "yp": "https://www.yelp.com/biz/77AI0iOrafQxa4e8-BNnww"},
 "2038910402960230": {"fb": "https://www.facebook.com/122205821171193", "ig": "https://www.instagram.com/explore/locations/122205821171193", "yp": "https://www.yelp.com/biz/8Egi2xKs7LlOMFQ6tVMPnA"},
}
SEARCH_TERM = {
    "barbershops": "barber", "plumbers": "plumber", "dentists": "dentist",
    "hvac": "HVAC repair", "auto repair": "auto repair",
    "cleaning services": "cleaning service", "roofing": "roofer",
    "garage doors": "garage door repair", "pet grooming": "pet groomer",
    "electricians": "electrician",
}
PROBLEM = {
    "none": "Right now, customers searching for {term} in {city} can't find you online — you have no website, so those customers call someone else.",
    "dead": "Right now, customers searching for {term} in {city} find your listing — but your website doesn't load, so they think you're closed and call someone else.",
    "weak": "Your website exists, but it's not bringing you customers — it doesn't show up well on Google, and visitors can't easily book or call from it.",
    "unknown": "Your online presence isn't bringing you customers from Google — visitors can't easily find, trust, or book you.",
    "ok": "Your website is up, but most local sites leak visitors — no clear booking path, no reviews on display, and invisible when customers ask AI for recommendations.",
}
def pitch_lines(r):
    term = SEARCH_TERM.get(r["category"], r["category"])
    prob = PROBLEM[r["website_status"]].format(term=term, city=r["city"])
    rc = int(r["review_count"] or 0)
    rating = float(r["rating"] or 0)
    if rc > 0 and rating >= 4.0:
        revline = f"Your {rating}★ Google reviews, shown right on your homepage — so new customers trust you before they call. Your Yelp reviews get the same spot."
    elif rc > 0:
        revline = "Your Google and Yelp reviews, shown right on your homepage — so new customers trust you before they call."
    else:
        revline = "A place for your Google and Yelp reviews, right on your homepage — so every happy customer builds trust for the next one."
    return [
        f"Hi, I'm Akash from Abhaa Inc. {prob}",
        "Here's what I build for you:",
        f"🔍 Found on Google — your site shows up when people search \"{term} near me\" in {r['city']}",
        f"💬 Answered by Google & AI — when people ask \"best {term} in {r['city']},\" Google and ChatGPT can recommend you",
        "📅 Book direct — customers book appointments straight from your site, even after hours",
        "📞 Tap to call — one tap on any phone, no number to remember",
        f"⭐ Reviews on display — {revline}",
        "Based on local search numbers, this can start bringing you 2–5 new inquiries a month, minimum.",
        "$1,000 a year — under $85 a month. One extra customer pays for the whole year.",
        "Can I show you a free demo in 5 minutes?",
    ]
STAGES = ["New", "Contacted", "Demo sent", "Follow-up", "Won", "Lost", "Not interested"]
COL_COLOR = {"New": "#38bdf8", "Contacted": "#ff8a3d", "Demo sent": "#a78bfa",
             "Follow-up": "#34d399", "Won": "#22c55e", "Lost": "#f87171", "Not interested": "#9a9ab0"}

def esc(s): return html.escape(str(s or ""), quote=True)
def site_type(url):
    if not url: return "none"
    host = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    if any(host == d or host.endswith("." + d) for d in DIRECTORY): return "listing"
    if any(host == d or host.endswith("." + d) for d in BUILDERS): return "builder"
    return "own"
def demo_url(r):
    slug = demo_slug.get(r["place_id"])
    if not slug: return ""
    return PREVIEW.get(slug, f"https://akashdeepsingh1.github.io/demos/sites/{slug}/")

# ---- LEADS blob (compact keys, same schema as before + st + soc) ----
leads = []
for r in rows:
    l = {"n": r["name"], "c": r["category"], "ct": r["city"], "s": r["state"],
         "p": r["phone"], "r": float(r["rating"] or 0), "rc": int(r["review_count"] or 0),
         "w": r["website"], "ws": r["website_status"], "pid": r["place_id"],
         "d": demo_url(r), "st": site_type(r["website"]), "pt": pitch_lines(r)}
    if r["place_id"] in SOCIALS:
        l["soc"] = SOCIALS[r["place_id"]]
    leads.append(l)
LEADS_JSON = json.dumps(leads, separators=(",", ":"), ensure_ascii=True)
assert "</script>" not in LEADS_JSON

# ---- static fallback cards (list view, plain links) ----
def static_card(r):
    pid = r["place_id"]
    phone = f'<a href="tel:{esc(r["phone"])}">📞 {esc(r["phone"])}</a>' if r["phone"] else '<span class="dim">No phone — use Google listing</span>'
    st = site_type(r["website"])
    site = f'<a href="{esc(r["website"])}" target="_blank" rel="noopener">{esc(r["website"])}</a> <span class="dim">({TYPE_LABEL[st]})</span>' if r["website"] else "No website"
    rc = int(r["review_count"] or 0)
    rating = float(r["rating"] or 0)
    rev = f"★{rating:.1f} Google ({rc} reviews)" if rc > 0 else "No Google reviews on file"
    d = demo_url(r)
    demo = f'<a href="{esc(d)}" target="_blank" rel="noopener">🎬 View demo</a>' if d else '<span class="dim">No demo yet</span>'
    gurl = ("https://www.google.com/maps/search/?api=1&query="
            + urllib.parse.quote(f"{r['name']} {r['city']}") + "&query_place_id=" + urllib.parse.quote(pid))
    pitch = "individual-pitches.html?q=" + urllib.parse.quote(r["name"])
    soc = ""
    if pid in SOCIALS:
        s = SOCIALS[pid]
        bits = []
        if s.get("fb"): bits.append(f'<a href="{esc(s["fb"])}" target="_blank" rel="noopener">Facebook</a>')
        if s.get("ig"): bits.append(f'<a href="{esc(s["ig"])}" target="_blank" rel="noopener">Instagram</a>')
        if s.get("yp"): bits.append(f'<a href="{esc(s["yp"])}" target="_blank" rel="noopener">Yelp</a>')
        if bits: soc = "<br>👥 Also on: " + " · ".join(bits)
    pitch_html = "<br>".join(esc(x) for x in pitch_lines(r))
    pitch_block = (f'<details style="margin-top:10px"><summary style="cursor:pointer;font-size:.88rem;color:#ff8ab0">📣 Sales pitch</summary>'
                   f'<div class="pitch">{pitch_html}</div></details>')
    bcls, blabel = {"none": ("b-none", "No website"), "dead": ("b-dead", "Dead URL"),
                    "weak": ("b-weak", "Weak site"), "unknown": ("b-unknown", "Unchecked"),
                    "ok": ("b-ok", "Live site")}.get(r["website_status"], ("b-unknown", "Unchecked"))
    opts = "".join(f'<option value="{s}"{" selected" if s == "New" else ""}>{s}</option>' for s in STAGES)
    return (
        f'<article class="card" data-pid="{esc(pid)}">'
        f'<div class="chead"><div><b>{esc(r["name"])}</b>'
        f'<div class="meta">{esc(r["city"])}, {esc(r["state"])} · {esc(r["category"])}</div></div>'
        f'<span class="badge {bcls}">{blabel}</span></div>'
        f'<div class="info">{phone} &nbsp;·&nbsp; <a href="{gurl}" target="_blank" rel="noopener">Google ↗</a><br>'
        f'🌐 {site}{soc}<br>⭐ {rev}<br>{demo}'
        f' &nbsp;·&nbsp; <a href="{pitch}" target="_blank" rel="noopener">📣 Find pitch</a></div>'
        f'{pitch_block}'
        f'<div class="track">'
        f'<div><label>Stage</label><select data-pid="{esc(pid)}" data-field="stage" onchange="setField(this)">{opts}</select></div>'
        f'<div><label>Last call</label><input type="date" data-pid="{esc(pid)}" data-field="last" value="" onchange="setField(this)"></div>'
        f'<div><label>Next follow-up</label><input type="date" data-pid="{esc(pid)}" data-field="next" value="" onchange="setField(this)"></div>'
        f'<div style="flex:1 1 180px"><label>Call outcome</label><input type="text" data-pid="{esc(pid)}" data-field="outcome" style="width:100%" placeholder="e.g. owner busy, call Tuesday" value="" oninput="setFieldDeb(this)"></div>'
        f'<div style="flex:1 1 100%"><label>Notes</label><textarea data-pid="{esc(pid)}" data-field="notes" placeholder="Free notes…" oninput="setFieldDeb(this)"></textarea></div>'
        f'<div class="saved" id="sv-{esc(pid)}"></div>'
        f'</div></article>'
    )
STATIC_CARDS = "\n".join(static_card(r) for r in rows)
cnt = Counter(r["website_status"] for r in rows)
COUNTS_HTML = (
    f'<span>Total leads: <b>{len(rows)}</b></span>'
    f'<span>No website: <b>{cnt.get("none", 0)}</b></span>'
    f'<span>Dead URL: <b>{cnt.get("dead", 0)}</b></span>'
    f'<span>Weak site: <b>{cnt.get("weak", 0)}</b></span>'
    f'<span>Unchecked: <b>{cnt.get("unknown", 0)}</b></span>'
    f'<span>Live site: <b>{cnt.get("ok", 0)}</b></span>'
    f'<span>With phone: <b>{sum(1 for r in rows if r["phone"])}</b></span>'
)
CITIES = sorted({r["city"] for r in rows})
CITY_OPTS = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in CITIES)

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0b13;color:#f0f0f6;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:20px 12px 60px}
.wrap{max-width:1200px;margin:0 auto}
h1{font-size:1.4rem;text-align:center}
.sub{color:#9a9ab0;text-align:center;font-size:.85rem;margin:4px 0 16px}
.counts{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:16px}
.counts span{background:#14141f;border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:5px 12px;font-size:.82rem}
.counts b{color:#fff}
.counts button{background:#14141f;border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:5px 12px;font-size:.82rem;color:#f0f0f6;cursor:pointer}
.counts button:hover{border-color:#ff8ab0}
.controls{background:#14141f;border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:14px;margin-bottom:16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.controls input[type=search]{flex:1 1 200px;background:#0b0b13;border:1px solid rgba(255,255,255,.15);border-radius:10px;color:#fff;padding:10px 12px;font-size:.92rem}
.controls select{background:#0b0b13;border:1px solid rgba(255,255,255,.15);border-radius:10px;color:#d9d9e8;padding:10px 8px;font-size:.88rem}
.controls button{background:#0b0b13;border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;padding:10px 14px;font-size:.88rem;cursor:pointer}
.controls button.on{background:#ff8ab0;color:#0b0b13;border-color:#ff8ab0;font-weight:700}
#shown{color:#9a9ab0;font-size:.85rem;margin-bottom:12px}
.card{background:#14141f;border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:16px;margin-bottom:12px}
.chead{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.chead b{font-size:1.02rem}
.meta{color:#9a9ab0;font-size:.82rem;margin-top:2px}
.badge{font-size:.72rem;font-weight:700;white-space:nowrap;border-radius:999px;padding:4px 10px}
.b-none{background:rgba(248,113,113,.15);color:#f87171;border:1px solid rgba(248,113,113,.4)}
.b-dead{background:rgba(255,138,61,.14);color:#ff8a3d;border:1px solid rgba(255,138,61,.45)}
.b-weak{background:rgba(255,209,102,.12);color:#ffd166;border:1px solid rgba(255,209,102,.4)}
.b-unknown{background:rgba(255,255,255,.07);color:#9a9ab0;border:1px solid rgba(255,255,255,.2)}
.b-ok{background:rgba(52,211,153,.14);color:#34d399;border:1px solid rgba(52,211,153,.45)}
.info{font-size:.88rem;line-height:1.6;color:#d9d9e8;margin-top:10px}
.info a{color:#ff8ab0}
.info .dim{color:#9a9ab0}
.track{border-top:1px solid rgba(255,255,255,.1);margin-top:12px;padding-top:12px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.track select,.track input[type=text],.track input[type=date]{background:#0b0b13;border:1px solid rgba(255,255,255,.15);border-radius:8px;color:#fff;padding:8px;font-size:.85rem}
.track textarea{background:#0b0b13;border:1px solid rgba(255,255,255,.15);border-radius:8px;color:#fff;padding:8px;font-size:.85rem;width:100%;min-height:52px;resize:vertical}
.track label{font-size:.75rem;color:#9a9ab0;display:block;margin-bottom:2px}
.saved{font-size:.75rem;color:#34d399;min-height:14px}
.due{font-size:.72rem;font-weight:700;color:#f87171}
.more{display:block;width:100%;background:#14141f;border:1px solid rgba(255,255,255,.2);border-radius:12px;color:#fff;padding:12px;font-size:.95rem;cursor:pointer;margin-top:4px}
/* kanban */
.kanban{display:flex;gap:12px;overflow-x:auto;align-items:flex-start;padding-bottom:12px}
.col{min-width:270px;flex:1 0 270px;background:#101018;border:1px solid rgba(255,255,255,.08);border-radius:14px;border-top:4px solid #9a9ab0;padding:10px}
.col h3{font-size:.9rem;margin:2px 4px 10px}
.col h3 span{color:#9a9ab0;font-weight:400}
.kcard{cursor:grab}
.kcard:active{cursor:grabbing}
.kcard .track{margin-top:10px}
.mini{background:#0b0b13;border:1px solid rgba(255,255,255,.2);border-radius:8px;color:#fff;padding:7px 11px;font-size:.83rem;cursor:pointer;margin:2px 2px 2px 0}
.mini:hover{border-color:#ff8ab0}
.fixnote{font-size:.75rem;color:#ffd166}
/* modal */
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.78);display:none;align-items:center;justify-content:center;z-index:50;padding:12px}
.overlay.open{display:flex}
.modalbox{width:96vw;max-width:1020px;height:88vh;background:#14141f;border:1px solid rgba(255,255,255,.15);border-radius:16px;display:flex;flex-direction:column;overflow:hidden}
.modalhead{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid rgba(255,255,255,.12)}
.modalhead b{flex:1;font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.modalhead a{color:#ff8ab0;font-size:.85rem;white-space:nowrap}
.modalhead button{background:#0b0b13;border:1px solid rgba(255,255,255,.25);border-radius:8px;color:#fff;padding:7px 12px;cursor:pointer}
.modalframe{flex:1;border:0;width:100%}
.fixform label{font-size:.8rem;color:#9a9ab0;display:block;margin:10px 0 4px}
.fixform input,.fixform select,.fixform textarea{width:100%;background:#0b0b13;border:1px solid rgba(255,255,255,.15);border-radius:8px;color:#fff;padding:9px;font-size:.9rem}
.fixform textarea{min-height:60px;resize:vertical}
.qlist{max-height:50vh;overflow:auto}
.qitem{border-bottom:1px solid rgba(255,255,255,.1);padding:10px 0;font-size:.87rem;line-height:1.5}
.pitch{font-size:.87rem;line-height:1.65;color:#d9d9e8;margin-top:6px}
"""

JS = r"""
var LS_KEY = "abhaa-crm-v1";
var FQ_KEY = "abhaa-crm-feedback";
var saved = {};
try { saved = JSON.parse(localStorage.getItem(LS_KEY) || "{}"); } catch(e) { saved = {}; }
var queue = [];
try { queue = JSON.parse(localStorage.getItem(FQ_KEY) || "[]"); } catch(e) { queue = []; }
function persist() { try { localStorage.setItem(LS_KEY, JSON.stringify(saved)); } catch(e) {} }
function persistQ() { try { localStorage.setItem(FQ_KEY, JSON.stringify(queue)); } catch(e) {} }
function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
function stOf(pid) { return (saved[pid] && saved[pid].stage) || "New"; }
function siteType(url) {
  if (!url) return "none";
  var host = url.replace(/^https?:\/\//, "").split("/")[0].toLowerCase().replace(/^www\./, "");
  var dir = ["yelp.com","facebook.com","instagram.com","rucat.net","barberboard.az.gov","chamberofcommerce.com","search.app","demandforce.com","worldorgs.com","dogdog.org","booksy.com","fresha.com","thumbtack.com","angi.com","homeadvisor.com","houzz.com","tripadvisor.com","yellowpages.com","yp.com","bbb.org","manta.com","mapquest.com","superpages.com","citysearch.com","local.com","groupon.com","nextdoor.com"];
  var bld = ["business.site","godaddysites.com","wixsite.com","weebly.com","jimdosite.com","dudaone.com","strikingly.com","webnode.com","site123.me"];
  for (var i = 0; i < dir.length; i++) { if (host === dir[i] || host.slice(-dir[i].length - 1) === "." + dir[i]) return "listing"; }
  for (var j = 0; j < bld.length; j++) { if (host === bld[j] || host.slice(-bld[j].length - 1) === "." + bld[j]) return "builder"; }
  return "own";
}
var TYPE_LABEL = {none: "No website", listing: "Listing page - not their own site", builder: "Simple builder site", own: "Own website"};
function disp(l) {
  var f = (saved[l.pid] && saved[l.pid].fixes) || {};
  var o = {};
  for (var k in l) o[k] = l[k];
  if (f.name) o.n = f.name;
  if (f.phone) o.p = f.phone;
  if (f.website) { o.w = f.website; o.st = siteType(f.website); }
  if (f.rating) o.r = parseFloat(f.rating);
  if (f.rc) o.rc = parseInt(f.rc, 10);
  if (f.ws) o.ws = f.ws;
  return o;
}
function badge(ws) {
  var map = {none: ["b-none", "No website"], dead: ["b-dead", "Dead URL"], weak: ["b-weak", "Weak site"], unknown: ["b-unknown", "Unchecked"], ok: ["b-ok", "Live site"]};
  var b = map[ws] || map.unknown;
  return '<span class="badge ' + b[0] + '">' + b[1] + "</span>";
}
function gmaps(l) {
  return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(l.n + " " + l.ct) + "&query_place_id=" + encodeURIComponent(l.pid);
}
function dueBadge(l) {
  var s = saved[l.pid];
  if (!s || !s.next) return "";
  var today = new Date(); today.setHours(0,0,0,0);
  var d = new Date(s.next + "T00:00:00");
  if (d <= today && stOf(l.pid) !== "Won" && stOf(l.pid) !== "Lost" && stOf(l.pid) !== "Not interested")
    return ' <span class="due">● follow-up due</span>';
  return "";
}
function infoHTML(l) {
  var phone = l.p ? '<a href="tel:' + esc(l.p) + '">📞 ' + esc(l.p) + "</a>"
    : '<span class="dim">No phone — use Google listing</span>';
  var site = l.w ? '<a href="' + esc(l.w) + '" target="_blank" rel="noopener">' + esc(l.w) + '</a> <span class="dim">(' + (TYPE_LABEL[l.st] || "Own website") + ")</span>" : "No website";
  var soc = "";
  if (l.soc) {
    var bits = [];
    if (l.soc.fb) bits.push('<a href="' + esc(l.soc.fb) + '" target="_blank" rel="noopener">Facebook</a>');
    if (l.soc.ig) bits.push('<a href="' + esc(l.soc.ig) + '" target="_blank" rel="noopener">Instagram</a>');
    if (l.soc.yp) bits.push('<a href="' + esc(l.soc.yp) + '" target="_blank" rel="noopener">Yelp</a>');
    if (bits.length) soc = "<br>👥 Also on: " + bits.join(" · ");
  }
  var rev = l.rc > 0 ? "★" + l.r.toFixed(1) + " Google (" + l.rc + " reviews)" : "No Google reviews on file";
  var demoBtn = l.d ? '<button class="mini" data-title="Demo - ' + esc(l.n) + '" data-url="' + esc(l.d) + '" onclick="openModalBtn(this)">🎬 View demo</button>'
    : '<span class="dim">No demo yet</span>';
  var pitchBtn = '<button class="mini" data-title="Pitch - ' + esc(l.n) + '" data-url="individual-pitches.html?q=' + encodeURIComponent(l.n) + '" onclick="openModalBtn(this)">📣 Find pitch</button>';
  return '<div class="info">' + phone + ' &nbsp;·&nbsp; <a href="' + gmaps(l) + '" target="_blank" rel="noopener">Google ↗</a><br>'
    + "🌐 " + site + soc + "<br>⭐ " + rev + "<br>" + demoBtn + " " + pitchBtn
    + ' <button class="mini" data-pid="' + esc(l.pid) + '" onclick="openFix(this)">✏️ Correct info</button></div>';
}
function pitchHTML(l) {
  if (!l.pt || !l.pt.length) return "";
  return '<details style="margin-top:10px"><summary style="cursor:pointer;font-size:.88rem;color:#ff8ab0">📣 Sales pitch</summary><div class="pitch">'
    + l.pt.map(function(x) { return esc(x); }).join("<br>") + "</div></details>";
}
function trackHTML(l, compact) {
  var s = saved[l.pid] || {};
  var stages = ["New","Contacted","Demo sent","Follow-up","Won","Lost","Not interested"];
  var opts = stages.map(function(st) { return '<option value="' + st + '"' + (stOf(l.pid) === st ? " selected" : "") + ">" + st + "</option>"; }).join("");
  var dp = 'data-pid="' + esc(l.pid) + '"';
  var inner = '<div><label>Stage</label><select ' + dp + ' data-field="stage" onchange="setField(this)">' + opts + "</select></div>"
    + '<div><label>Last call</label><input type="date" ' + dp + ' data-field="last" value="' + esc(s.last || "") + '" onchange="setField(this)"></div>'
    + '<div><label>Next follow-up</label><input type="date" ' + dp + ' data-field="next" value="' + esc(s.next || "") + '" onchange="setField(this)"></div>'
    + '<div style="flex:1 1 180px"><label>Call outcome</label><input type="text" ' + dp + ' data-field="outcome" style="width:100%" placeholder="e.g. owner busy, call Tuesday" value="' + esc(s.outcome || "") + '" oninput="setFieldDeb(this)"></div>'
    + '<div style="flex:1 1 100%"><label>Notes</label><textarea ' + dp + ' data-field="notes" placeholder="Free notes…" oninput="setFieldDeb(this)">' + esc(s.notes || "") + "</textarea></div>"
    + '<div class="saved" id="sv-' + l.pid + '"></div>';
  if (compact) return '<details style="margin-top:10px"><summary style="cursor:pointer;font-size:.85rem;color:#9a9ab0">Call tracking</summary><div class="track">' + inner + "</div></details>";
  return '<div class="track">' + inner + "</div>";
}
function kanbanCardHTML(raw) {
  var l = disp(raw);
  var fixNote = (saved[l.pid] && saved[l.pid].fixes) ? ' <span class="fixnote">(corrected info)</span>' : "";
  return '<article class="card kcard" draggable="true" ondragstart="dragStart(event)" data-pid="' + esc(l.pid) + '">'
    + '<div class="chead"><div><b>' + esc(l.n) + "</b>" + fixNote + dueBadge(l)
    + '<div class="meta">' + esc(l.ct) + ", " + esc(l.s) + " · " + esc(l.c) + "</div></div>" + badge(l.ws) + "</div>"
    + infoHTML(l) + pitchHTML(l) + trackHTML(l, true) + "</article>";
}
function listCardHTML(raw) {
  var l = disp(raw);
  var fixNote = (saved[l.pid] && saved[l.pid].fixes) ? ' <span class="fixnote">(corrected info)</span>' : "";
  return '<article class="card" data-pid="' + esc(l.pid) + '">'
    + '<div class="chead"><div><b>' + esc(l.n) + "</b>" + fixNote + dueBadge(l)
    + '<div class="meta">' + esc(l.ct) + ", " + esc(l.s) + " · " + esc(l.c) + "</div></div>" + badge(l.ws) + "</div>"
    + infoHTML(l) + pitchHTML(l) + trackHTML(l, false) + "</article>";
}
var STAGES = ["New","Contacted","Demo sent","Follow-up","Won","Lost","Not interested"];
var COL_COLOR = {"New": "#38bdf8", "Contacted": "#ff8a3d", "Demo sent": "#a78bfa", "Follow-up": "#34d399", "Won": "#22c55e", "Lost": "#f87171", "Not interested": "#9a9ab0"};
var view = "kanban";
var filtered = [], shownCount = 0, PAGE = 100, saveTimer = null;
function setField(el) {
  var pid = el.getAttribute("data-pid"), field = el.getAttribute("data-field");
  saved[pid] = saved[pid] || {};
  saved[pid][field] = el.value;
  persist();
  var sEl = document.getElementById("sv-" + pid);
  if (sEl) sEl.textContent = "✓ Saved";
  if (field === "stage") { render(); } else { renderCounts(); }
}
function setFieldDeb(el) {
  var pid = el.getAttribute("data-pid"), field = el.getAttribute("data-field");
  saved[pid] = saved[pid] || {};
  saved[pid][field] = el.value;
  clearTimeout(saveTimer);
  saveTimer = setTimeout(function() {
    persist();
    var sEl = document.getElementById("sv-" + pid);
    if (sEl) sEl.textContent = "✓ Saved";
    renderCounts();
  }, 600);
}
function setStatusFilter(ws) {
  document.getElementById("fStatus").value = ws;
  render();
}
function setStageFilter(st) {
  document.getElementById("fStage").value = st;
  render();
}
function clearFilters() {
  document.getElementById("fStatus").value = "";
  document.getElementById("fStage").value = "";
  document.getElementById("fCity").value = "";
  document.getElementById("q").value = "";
  render();
}
function renderCounts() {
  var byStatus = {}, byStage = {}, withPhone = 0;
  LEADS.forEach(function(raw) {
    var l = disp(raw);
    byStatus[l.ws] = (byStatus[l.ws] || 0) + 1;
    var st = stOf(l.pid);
    byStage[st] = (byStage[st] || 0) + 1;
    if (l.p) withPhone++;
  });
  var sp = function(label, ws, n) { return '<button class="pill" onclick="setStatusFilter(\'' + ws + '\')">' + label + ": <b>" + n + "</b></button>"; };
  var tp = function(st, n) { return '<button class="pill" onclick="setStageFilter(\'' + st + '\')">' + st + ": <b>" + n + "</b></button>"; };
  var stagePills = STAGES.filter(function(st) { return byStage[st]; }).map(function(st) { return tp(st, byStage[st]); }).join("");
  document.getElementById("counts").innerHTML =
    '<button class="pill" onclick="clearFilters()">Total leads: <b>' + LEADS.length + "</b></button>"
    + sp("No website", "none", byStatus.none || 0)
    + sp("Dead URL", "dead", byStatus.dead || 0)
    + sp("Weak site", "weak", byStatus.weak || 0)
    + sp("Unchecked", "unknown", byStatus.unknown || 0)
    + sp("Live site", "ok", byStatus.ok || 0)
    + "<span>With phone: <b>" + withPhone + "</b></span>"
    + stagePills;
}
function getFiltered() {
  var q = document.getElementById("q").value.toLowerCase();
  var fs = document.getElementById("fStatus").value;
  var ft = document.getElementById("fStage").value;
  var fc = document.getElementById("fCity").value;
  var sort = document.getElementById("sort").value;
  var out = LEADS.filter(function(raw) {
    var l = disp(raw);
    if (fs && l.ws !== fs) return false;
    if (ft && stOf(l.pid) !== ft) return false;
    if (fc && l.ct !== fc) return false;
    if (q && (l.n + " " + l.ct + " " + l.c).toLowerCase().indexOf(q) === -1) return false;
    return true;
  });
  if (sort === "reviews") out.sort(function(a, b) { return disp(b).rc - disp(a).rc || disp(a).n.localeCompare(disp(b).n); });
  if (sort === "name") out.sort(function(a, b) { return disp(a).n.localeCompare(disp(b).n); });
  if (sort === "city") out.sort(function(a, b) { return (disp(a).ct + disp(a).n).localeCompare(disp(b).ct + disp(b).n); });
  return out;
}
function renderKanban() {
  var groups = {};
  STAGES.forEach(function(st) { groups[st] = []; });
  filtered.forEach(function(raw) { groups[stOf(raw.pid)].push(raw); });
  var html = "";
  STAGES.forEach(function(st) {
    var cards = groups[st].slice().sort(function(a, b) { return disp(b).rc - disp(a).rc; });
    html += '<div class="col" style="border-top-color:' + COL_COLOR[st] + '" ondragover="event.preventDefault()" ondrop="dropCard(event, \'' + st + '\')">'
      + "<h3>" + st + " <span>(" + cards.length + ")</span></h3>"
      + cards.map(kanbanCardHTML).join("") + "</div>";
  });
  document.getElementById("kanban").innerHTML = html;
  document.getElementById("shown").textContent = "Kanban: " + filtered.length + " leads shown";
}
function renderList() {
  shownCount = 0;
  var sk = document.getElementById("staticKanban");
  if (sk) sk.style.display = "none";
  document.getElementById("list").innerHTML = "";
  loadMore();
}
function loadMore() {
  var slice = filtered.slice(shownCount, shownCount + PAGE);
  var html = slice.map(listCardHTML).join("");
  document.getElementById("list").insertAdjacentHTML("beforeend", html);
  shownCount += slice.length;
  document.getElementById("shown").textContent = "Showing " + shownCount + " of " + filtered.length + " leads";
  document.getElementById("moreBtn").style.display = shownCount < filtered.length ? "" : "none";
}
function render() {
  filtered = getFiltered();
  renderCounts();
  updateQueueBtn();
  if (view === "kanban") {
    document.getElementById("kanban").style.display = "flex";
    document.getElementById("listView").style.display = "none";
    document.getElementById("moreBtn").style.display = "none";
    renderKanban();
  } else {
    document.getElementById("kanban").style.display = "none";
    document.getElementById("listView").style.display = "";
    renderList();
  }
  document.getElementById("btnKanban").className = view === "kanban" ? "on" : "";
  document.getElementById("btnList").className = view === "list" ? "on" : "";
}
function setView(v) { view = v; render(); }
function dragStart(ev) {
  var card = ev.target.closest ? ev.target.closest(".kcard") : null;
  if (card) ev.dataTransfer.setData("text/plain", card.getAttribute("data-pid"));
}
function dropCard(ev, stage) {
  ev.preventDefault();
  var pid = ev.dataTransfer.getData("text/plain");
  if (!pid) return;
  saved[pid] = saved[pid] || {};
  saved[pid].stage = stage;
  persist();
  render();
}
function openModalBtn(el) {
  openModal(el.getAttribute("data-title"), el.getAttribute("data-url"));
}
function openModal(title, url) {
  document.getElementById("modalTitle").textContent = title;
  document.getElementById("modalFrame").src = url;
  document.getElementById("modalLink").href = url;
  document.getElementById("modal").className = "overlay open";
}
function closeModal() {
  document.getElementById("modal").className = "overlay";
  document.getElementById("modalFrame").src = "about:blank";
}
document.addEventListener("keydown", function(ev) { if (ev.key === "Escape") { closeModal(); closeFix(); closeQueue(); } });
var fixPid = null;
function openFix(el) {
  fixPid = el.getAttribute("data-pid");
  var lead = null;
  for (var i = 0; i < LEADS.length; i++) { if (LEADS[i].pid === fixPid) { lead = LEADS[i]; break; } }
  document.getElementById("fixName").textContent = lead ? lead.n : fixPid;
  document.getElementById("fixField").value = "rc";
  document.getElementById("fixValue").value = "";
  document.getElementById("fixNote").value = "";
  document.getElementById("fixModal").className = "overlay open";
}
function closeFix() { document.getElementById("fixModal").className = "overlay"; }
function saveFix() {
  var field = document.getElementById("fixField").value;
  var value = document.getElementById("fixValue").value.trim();
  var note = document.getElementById("fixNote").value.trim();
  if (!value) { alert("Enter the correct value first."); return; }
  if (field === "ws" && ["none","dead","weak","unknown","ok"].indexOf(value) === -1) {
    alert("For website status use one of: none, dead, weak, unknown, ok"); return;
  }
  if (field === "rating" && isNaN(parseFloat(value))) { alert("Rating must be a number, e.g. 4.5"); return; }
  if (field === "rc" && isNaN(parseInt(value, 10))) { alert("Review count must be a whole number"); return; }
  var lead = null;
  for (var i = 0; i < LEADS.length; i++) { if (LEADS[i].pid === fixPid) { lead = LEADS[i]; break; } }
  var oldVal = lead ? lead[field === "rc" ? "rc" : field === "rating" ? "r" : field === "ws" ? "ws" : field] : "";
  if (field === "name") oldVal = lead.n;
  if (field === "phone") oldVal = lead.p;
  if (field === "website") oldVal = lead.w;
  saved[fixPid] = saved[fixPid] || {};
  saved[fixPid].fixes = saved[fixPid].fixes || {};
  saved[fixPid].fixes[field] = value;
  queue.push({pid: fixPid, name: lead ? lead.n : fixPid, field: field, old: String(oldVal == null ? "" : oldVal), val: value, note: note, at: new Date().toISOString().slice(0, 10)});
  persist(); persistQ();
  closeFix();
  render();
  alert("Saved on this card, and queued for the master data. Tap Feedback queue, then Export, and send it to Muse to update the master file.");
}
function updateQueueBtn() {
  var el = document.getElementById("qcount");
  if (el) el.textContent = queue.length;
}
function openQueue() {
  var box = document.getElementById("queueList");
  if (!queue.length) { box.innerHTML = "<p>No pending corrections yet. Use ✏️ Correct info on any card to add one.</p>"; }
  else {
    box.innerHTML = queue.map(function(e, i) {
      return '<div class="qitem"><b>' + esc(e.name) + "</b> — " + esc(e.field) + ": <span style='color:#9a9ab0'>" + esc(e.old) + "</span> → <b>" + esc(e.val) + "</b>"
        + (e.note ? "<br><span style='color:#9a9ab0'>" + esc(e.note) + "</span>" : "")
        + "<br><span style='color:#9a9ab0;font-size:.78rem'>" + esc(e.at) + "</span></div>";
    }).join("");
  }
  document.getElementById("queueModal").className = "overlay open";
}
function closeQueue() { document.getElementById("queueModal").className = "overlay"; }
function exportFeedback() {
  if (!queue.length) { alert("Nothing to export yet."); return; }
  var text = JSON.stringify(queue, null, 2);
  var blob = new Blob([text], {type: "application/json"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "crm-feedback.json";
  a.click();
  try {
    var summary = queue.map(function(e) { return e.name + " | " + e.field + ": " + e.old + " -> " + e.val + (e.note ? " (" + e.note + ")" : ""); }).join("\n");
    navigator.clipboard.writeText(summary);
  } catch(e) {}
  alert("Exported crm-feedback.json and copied a summary. Send either one to Muse and I will update the master prospect file, dashboard, and pitch book.");
}
function clearQueue() {
  if (!confirm("Clear all queued corrections? Only do this after Muse has applied them.")) return;
  queue = [];
  persistQ();
  openQueue();
  render();
}
function exportNotes() {
  var data = {app: "abhaa-crm", version: 1, exportedAt: new Date().toISOString(), saved: saved, queue: queue};
  var text = JSON.stringify(data, null, 2);
  var blob = new Blob([text], {type: "application/json"});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "crm-notes-backup.json";
  a.click();
  alert("Notes backup downloaded (crm-notes-backup.json). Keep it safe — it restores your stages, dates, outcomes, notes, corrections, and feedback queue on any file or device.");
}
function applyImported(obj) {
  var count = 0;
  if (obj && obj.saved && typeof obj.saved === "object") {
    for (var pid in obj.saved) {
      var old = saved[pid] || {};
      var incoming = obj.saved[pid] || {};
      var merged = {};
      for (var k in old) merged[k] = old[k];
      for (var k2 in incoming) merged[k2] = incoming[k2];
      if (incoming.fixes && old.fixes) {
        var fx = {};
        for (var f in old.fixes) fx[f] = old.fixes[f];
        for (var f2 in incoming.fixes) fx[f2] = incoming.fixes[f2];
        merged.fixes = fx;
      }
      saved[pid] = merged;
      count++;
    }
  }
  if (obj && obj.queue && obj.queue.length) {
    for (var i = 0; i < obj.queue.length; i++) queue.push(obj.queue[i]);
  }
  return count;
}
function importNotes(ev) {
  var file = ev.target.files && ev.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function() {
    try {
      var obj = JSON.parse(reader.result);
      if (!obj || typeof obj.saved !== "object") { alert("That file is not a CRM notes backup."); return; }
      var n = applyImported(obj);
      persist(); persistQ();
      render();
      alert("Imported notes for " + n + " leads" + (obj.queue && obj.queue.length ? " and " + obj.queue.length + " queued feedback items." : "."));
    } catch (e) { alert("Could not read that backup file."); }
  };
  reader.readAsText(file);
  ev.target.value = "";
}
render();
"""

STATIC_KANBAN = "".join(
    f'<div class="col" style="border-top-color:{COL_COLOR[s]};min-width:270px;flex:1 0 270px"><h3>{s} <span>({len(rows) if s == "New" else 0})</span></h3>'
    + (STATIC_CARDS if s == "New" else "") + "</div>"
    for s in STAGES
)
STATIC_NOTE = (f"<p><b>Kanban board:</b> New ({len(rows)}) · Contacted (0) · Demo sent (0) · Follow-up (0) · Won (0) · Lost (0) · Not interested (0) — "
               "scroll sideways to see all 7 columns.</p>"
               "<p class=\"sub\">Panel view: every lead sits in New here — open this file in a browser "
               "for your saved stages, drag-and-drop, and the popup demo/pitch viewer.</p>")
STATUS_OPTS = ("<option value=\"\">All website statuses</option>"
    "<option value=\"none\">No website</option><option value=\"dead\">Dead URL</option>"
    "<option value=\"weak\">Weak site</option><option value=\"unknown\">Unchecked</option>"
    "<option value=\"ok\">Live site</option>")
STAGE_OPTS = "<option value=\"\">All stages</option>" + "".join(
    f'<option value="{s}">{s}</option>' for s in STAGES)
SORT_OPTS = ("<option value=\"reviews\">Sort: most reviews first</option>"
    "<option value=\"name\">Sort: name A-Z</option><option value=\"city\">Sort: city</option>")

MODALS = """
<div class="overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modalbox">
    <div class="modalhead"><b id="modalTitle"></b><a id="modalLink" href="#" target="_blank" rel="noopener">Open in new tab ↗</a><button onclick="closeModal()">✕ Close</button></div>
    <iframe class="modalframe" id="modalFrame" src="about:blank"></iframe>
  </div>
</div>
<div class="overlay" id="fixModal" onclick="if(event.target===this)closeFix()">
  <div class="modalbox" style="height:auto;max-height:88vh">
    <div class="modalhead"><b id="fixName">Correct info</b><button onclick="closeFix()">✕ Close</button></div>
    <div class="fixform" style="padding:16px;overflow:auto">
      <label>What is wrong?</label>
      <select id="fixField">
        <option value="rc">Review count</option>
        <option value="rating">Google rating</option>
        <option value="phone">Phone</option>
        <option value="website">Website</option>
        <option value="ws">Website status (none, dead, weak, unknown, ok)</option>
        <option value="name">Business name</option>
      </select>
      <label>Correct value</label>
      <input id="fixValue" type="text" placeholder="e.g. 42">
      <label>Note (optional)</label>
      <textarea id="fixNote" placeholder="e.g. counted on the Google listing today"></textarea>
      <div style="margin-top:14px"><button class="mini" onclick="saveFix()">💾 Save correction</button></div>
      <p style="color:#9a9ab0;font-size:.82rem;margin-top:10px">This updates the card right away and queues the fix for the master data. Export the queue and send it to Muse to update the source file, dashboard, and pitch book.</p>
    </div>
  </div>
</div>
<div class="overlay" id="queueModal" onclick="if(event.target===this)closeQueue()">
  <div class="modalbox" style="height:auto;max-height:88vh">
    <div class="modalhead"><b>Feedback queue</b><button onclick="closeQueue()">✕ Close</button></div>
    <div style="padding:16px"><div class="qlist" id="queueList"></div>
    <div style="margin-top:14px;display:flex;gap:8px"><button class="mini" onclick="exportFeedback()">⬇️ Export</button><button class="mini" onclick="clearQueue()">🗑️ Clear queue</button></div>
    <p style="color:#9a9ab0;font-size:.82rem;margin-top:10px">Send the export to Muse and the master prospect file, dashboard, and pitch book get updated.</p></div>
  </div>
</div>
"""

PAGE = (
"<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
"<title>CRM — Website Sales Leads</title>\n<style>" + BASE_CSS + "</style></head>\n<body>\n<div class=\"wrap\">\n"
"<h1>📋 Sales CRM</h1>\n"
'<p class="sub">Abhaa Inc — $1,000/year websites · tap a phone number to call · notes save automatically on this device'
f' · Build {STAMP} · Kanban board + pitch on every card</p>'
f'<div class="counts" id="counts">{COUNTS_HTML}</div>\n'
"<div class=\"controls\">\n"
"<input id=\"q\" type=\"search\" placeholder=\"Search name, city, category…\" oninput=\"render()\">\n"
f'<select id="fStatus" onchange="render()">{STATUS_OPTS}</select>\n'
f'<select id="fStage" onchange="render()">{STAGE_OPTS}</select>\n'
f'<select id="fCity" onchange="render()"><option value="">All cities</option>{CITY_OPTS}</select>\n'
f'<select id="sort" onchange="render()">{SORT_OPTS}</select>\n'
"<button id=\"btnKanban\" onclick=\"setView('kanban')\">Kanban</button>\n"
"<button id=\"btnList\" onclick=\"setView('list')\">List</button>\n"
"<button onclick=\"openQueue()\">📝 Feedback queue (<span id=\"qcount\">0</span>)</button>\n"
"<button onclick=\"exportNotes()\">💾 Export notes</button>\n"
"<button onclick=\"document.getElementById('importFile').click()\">📥 Import notes</button>\n"
"<input type=\"file\" id=\"importFile\" accept=\".json\" style=\"display:none\" onchange=\"importNotes(event)\">\n"
"</div>\n"
"<div class=\"kanban\" id=\"kanban\"></div>\n"
f'<div id="listView">{STATIC_NOTE}<div class="kanban" id="staticKanban" style="display:flex;gap:12px;overflow-x:auto;align-items:flex-start;padding-bottom:12px">\n{STATIC_KANBAN}\n</div><div id="list"></div></div>\n'
f'<div id="shown">Kanban (panel view): {len(rows)} leads, all in New</div>\n'
"<button class=\"more\" id=\"moreBtn\" onclick=\"loadMore()\" style=\"display:none\">Load more</button>\n"
+ MODALS +
"</div>\n<script>\nvar LEADS = " + LEADS_JSON + ";\n" + JS + "\n</script>\n</body></html>\n"
)
open(os.path.join(BASE, "crm.html"), "w").write(PAGE)
shutil.copy(os.path.join(BASE, "crm.html"), os.path.join(BASE, "crm-kanban-" + STAMP[:10] + ".html"))
print("wrote crm.html:", len(PAGE), "chars,", len(rows), "leads")
