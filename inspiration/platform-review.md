# Platform review: InVideo, ImagineArt, CapCut (and what they miss)

Researched 23 September 2026, read-only (no sign-ups, no logins). Phase: **Develop** (choosing the tooling for the spider piece).
Sources are official pages unless marked **[3P]** (third-party report) or **[unverified]** (could not confirm from an official page).
USD to GBP at roughly $1 = £0.75 where only USD is published; treat those as approximate.

---

**TL;DR:** None of the three is the right editor for this work. InVideo and ImagineArt are **AI generation storefronts** with a thin editor attached; CapCut is a real desktop timeline editor but built for social cuts, with an aggressive content licence. The lean stack is **DaVinci Resolve (free) for video, Affinity (free) for stills, and fal.ai pay-per-clip for generation**, on top of the Codex stills you already get free. Fixed cost **£0 a month**; variable cost about **£8 to £15 a month** at 20 clips. Upgrade only when a specific wall is hit (Resolve Studio one-off, or After Effects if the azatstr plugin look becomes essential).

---

## 1. What each one actually is

| | InVideo (invideo.io) | ImagineArt (imagine.art) | CapCut (capcut.com) |
|---|---|---|---|
| **Category** | AI video agent + generation reseller, with a browser timeline bolted on | AI image/video generation reseller with a node canvas ("Workflows") | Timeline editor (ByteDance), with Dreamina/Seedance generation bolted on |
| **Mac desktop app** | No. Browser only; apps listed are iOS/Android **[unverified for Mac]** | No. Web plus mobile; plugins for Premiere, After Effects, Figma, Framer | **Yes.** CapCut Desktop, macOS 10.14+ |
| **Core promise** | "Edit by typing a command"; agents for script, edit, colour, sound | 50+ models on one credit wallet; Film Studio camera controls | Fast social editing, templates, auto-captions |
| **Owner / jurisdiction** | Whitesheep Technology (India) | Vyro / ImagineArt | Bytedance Pte. Ltd. (Singapore) |

## 2. Timeline editing depth (the part Dex needs)

| Capability | InVideo | ImagineArt | CapCut Desktop | DaVinci Resolve (free) | After Effects |
|---|---|---|---|---|---|
| Multi-track layers | Yes | No real timeline (Compositor node, trimmer, "combine videos") | Yes | Yes | Yes (comps) |
| Keyframes / curves | Claimed **[3P]** | No | Yes, "keyframes and graphs" (official) | Yes, full curve editor | Yes, graph editor |
| Masks | AI object/background replace; manual masks **[unverified]** | Prompt-based edit only | Yes; AI masks on Pro **[3P]** | Yes, plus Fusion rotoscoping | Yes |
| Blend modes | **[unverified]** | No | Yes **[3P]** | Yes (Edit page and Fusion Merge) | Yes |
| Motion tracking | **[unverified]** | No | Yes, "Motion tracking" tool (official) | Yes: point and **planar tracker free**; camera tracker Studio only | Yes, plus Mocha |
| Speed ramps | Claimed **[3P]** | No | Yes | Yes, retime curves | Yes |
| 4K export | Paid plans, from Starter (official) | Generation to 4K on Ultimate+ | Pro only **[3P]** | Yes, UHD at up to 60 fps free (official) | Yes |
| Alpha / ProRes 4444 | **[unverified]**; exports timeline XML to Premiere, Resolve, FCP (official) | No | No ProRes 4444; alpha only via HEVC/WebM on desktop **[3P]** | Yes on Mac (ProRes 4444 with alpha) **[3P]** | Yes |
| Frame rate | **[unverified]** | Model-dependent | Up to 60 fps on Pro **[3P]** | Up to 60 fps free, 120 fps Studio (official) | Any |
| Verdict for HUD-over-nature compositing | Weak | Not an editor | Adequate for cuts, weak for compositing | **Strong** | **Strongest**, but subscription |

The deciding row is **alpha**. The HUD and tracking layers will come out of TouchDesigner and Blender as ProRes 4444 or PNG sequences with transparency. An editor that cannot take and keep alpha cleanly, with blend modes and a tracker to pin overlays to a moving spider, is the wrong tool whatever else it does.

## 3. Static design ability

| | InVideo | ImagineArt | CapCut | Affinity (Canva) | Figma | Photoshop |
|---|---|---|---|---|---|---|
| Layered raster editing | No | Prompt edits, upscale, background removal | Basic image editor (web) | Yes: layers, masks, blend modes, PSD in/out | Limited raster | Yes |
| Layout / type | No | Carousel maker, Ad Maker | Templates | Yes (Publisher functions merged in) | **Best for layout, social templates** | Adequate |
| Mac native | No | No | Yes | Yes | Desktop app (Electron) | Yes |
| Cost | n/a | n/a | n/a | **Free**; AI features need Canva Pro (~$18/mo) **[3P]** | Free Starter; Professional **£14/mo** full seat | **£21.98/mo** single app (25 gen credits); Photography plan £19.97/mo |

## 4. Which generation models they resell, and at what cost

| | InVideo | ImagineArt | CapCut |
|---|---|---|---|
| Video models | Seedance 2.0 / 2.0 Fast / 2.5 on plan pages; model pages for Veo 3.1, Sora 2, Kling, Wan, Pixverse, Hailuo | Kling 2.1 to 3.0 (incl. 3.0 4K, O1, O3), Veo 3.1 (Lite/Fast/full), Sora 2 / 2 Pro, Seedance 1.x to 2.5, Runway 4.5, Luma Ray 2, Hailuo, Wan, PixVerse, Grok, LTX 2.3 | Dreamina Seedance 2.0 / 2.5 (ByteDance's own) |
| Image models | Nano Banana Pro, GPT Image 2, Flux Kontext, Seedream, Ideogram, Imagen, Reve | Flux 2 / Kontext / 1.1 Ultra, Nano Banana, GPT Image 2, Seedream, ImagineArt's own | Dreamina (Seedream) |
| Example credit cost | Seedance 2.0 Fast 720p ≈ 30 cr / 5 s; Seedance 2.5 1080p ≈ 50 cr / 5 s; Nano Banana Pro ≈ 2.5 cr | Kling 3.0 Pro 300 cr base; Kling 3.0 4K 755; Veo 3.1 900; Veo 3.1 Fast 350; Sora 2 Pro 720 | Bundled Pro credits **[unverified]** |
| Rough $ per Kling-class 5 s clip | Starter: 400 cr for $20 → Seedance 2.0 Fast ≈ **$1.50** | Basic: 3,000 cr for $13 → Kling 3.0 Pro ≈ **$1.30** | n/a |
| Same clip direct on fal.ai | Kling v3 Pro **$0.56** (5 s, audio off); Veo 3.1 1080p **$1.00** audio off, $2.00 audio on | | |
| Rollover | Credits do not roll over | Credits do not roll over | **[unverified]** |

Resellers roughly double the per-clip price, lock credits to a monthly expiry, and gate the better models behind the upper tiers (Veo on ImagineArt needs Ultimate; Seedance 2.0 at 4K on InVideo needs Plus).

## 5. Pricing tiers (current, 23 Sep 2026)

| Plan | InVideo (per seat, annual / monthly) | ImagineArt (USD docs, monthly) | ImagineArt (UK live page, annual, per month) | CapCut |
|---|---|---|---|---|
| Free | Yes: watermark, weekly export limits, 720p **[3P for 720p]** | 100 credits/day, standard models only | £0 | Yes, up to 1080p |
| Entry | Starter **$20 / $20**, 400 cr, 20 GB | Basic **$13**, 3,000 cr, 768p video | Basic £6 | Standard ~$9.99 **[3P]** |
| Mid | Plus **$50 / $60**, 2,000 cr, 4K Seedance 2.0 | Standard **$30**, 8,000 cr, 1080p, private gens | Standard £14 | Pro **£21.99/mo** or £199.99/yr UK; $19.99 US **[3P, price is region-set and only visible after login]** |
| Top | Max **$100 / $150**, 5,000 cr | Ultimate **$50**, 16,000 cr, 4K, Veo; Creator $250 | Ultimate £25; Creator £61 | Teams **[unverified]** |

ImagineArt's own docs and live page disagree on price; the live page wins. InVideo's "timeline editing uses no credits", so the Starter seat is effectively a $20 browser editor plus 400 generation credits.

## 6. Licence, ownership, watermark

| | InVideo | ImagineArt | CapCut |
|---|---|---|---|
| Who owns outputs | **You.** Invideo assigns its rights in Outputs "to the extent we are able", plus a perpetual commercial licence that survives cancellation | **ImagineArt keeps title to generated content** and grants you a licence; paid plans may use commercially, free is personal only | "We don't own your User Content" |
| What they take from you | Narrow licence to host and process; will not train on your data | Perpetual, irrevocable, **sublicensable** licence over Your Content, including to "promote" the platform. Basic plan generations are **public**; private needs Standard+. Training is opt-in | Perpetual, sublicensable, transferable licence to use, modify and distribute your content for "developing" the Services, **plus a licence to your name, image and likeness, including in sponsored content** (terms dated 15 Apr 2026) |
| Free-tier watermark | Yes (official FAQ) | Yes on free images **[3P]** | Only on Pro-badged templates/effects, plus a removable end card **[3P]** |
| Risk for original art | Low | Medium: public-by-default on Basic, non-assignment of title | Medium to high for unreleased original work |

## 7. Known limits and red flags

| Platform | Limits worth knowing |
|---|---|
| **InVideo** | Browser only, so large ProRes/alpha sources from TouchDesigner must upload to the cloud. Per-seat team pricing even for one person. Credit prices "may be updated at any time, without prior notice". The value is the agent and the Seedance credits, not the editor. |
| **ImagineArt** | Not an editor. Video length capped per tier (3 to 6 s on Basic). Public gallery on the cheapest plan. Two price lists that disagree. The useful part is the After Effects and Figma plugins, which only matter if you already live in those apps. |
| **CapCut** | Real Mac app, genuinely fast. But: no ProRes 4444, alpha is awkward, compositing is shallow, 4K sits behind a £22/mo Pro, the price is only shown after login, and the June 2025 / April 2026 licence covers drafts and your likeness. US availability has been politically unstable. |

## 8. The alternatives he may be missing

| Tool | What it gives this work | Cost | Why it matters here |
|---|---|---|---|
| **DaVinci Resolve (free)** | Edit, colour, Fairlight audio and **Fusion** (node compositing, like TouchDesigner's mental model) in one Mac app. Planar and point trackers, blend modes, keyframe curves, ProRes 4444 alpha, UHD 60 fps | **£0**. Studio $295 one-off adds Magic Mask, camera tracker, AI noise reduction, 120 fps | The node graph maps directly onto how Dex already thinks in TouchDesigner and Blender compositor |
| **After Effects** | Industry standard for HUD/motion design; the plugin ecosystem azatstr uses (Motion Extractor is pay-what-you-want, suggested **$39.99**) | **£21.98/mo** single app (annual, billed monthly); CC Pro £66.49/mo | Worth it only if the plugin look becomes central. Motion Extractor is essentially a time-offset difference blend, which Fusion and TouchDesigner can both build natively |
| **Premiere Pro** | Editor that pairs with AE | ~£21.98/mo single app **[unverified GBP]** | Redundant if Resolve is the editor |
| **Affinity (Canva)** | Full Photoshop-class raster, vector and layout, Mac native, PSD round-trip | **£0** (AI features need a Canva subscription) | Replaces Photoshop for dark composited stills |
| **Figma** | Layout, social templates, type systems | Free Starter; £14/mo Professional | Keep on the free tier for carousels if already in use |
| **fal.ai** | Direct API access to Kling v3 Pro, Veo 3.1, Flux, Seedance at list price, pay per clip, commercial use allowed | Kling v3 Pro $0.112/s; Veo 3.1 $0.20 to $0.60/s | Matches the existing image-engine routing (Kling via fal, Veo when audio is needed) and the spend gate |
| **Krea** | Multi-model generation plus real-time canvas | Free; Pro from $21/mo; Max $63/mo | A reseller like ImagineArt, with a better real-time sketch-to-image tool. Optional |
| **Higgsfield** | Multi-model reseller strong on camera-move presets | Starter $19/mo (270 cr); Plus $47 annual / $59 monthly; Ultra $99 / $129 | Another subscription wallet; not needed if fal covers the models |

## 9. Recommendation: the lean stack

| Job | Pick | Monthly cost | Why this one |
|---|---|---|---|
| **Video edit + compositing** | **DaVinci Resolve (free)**, Mac native on the M5 Pro | **£0** | Only free option that takes TouchDesigner/Blender alpha cleanly, tracks the spider, blends the HUD and exports ProRes. Fusion is node-based like TouchDesigner. Upgrade to Studio ($295 one-off, no subscription) only if Magic Mask or the 3D camera tracker is needed |
| **Static design** | **Affinity (free)**; Figma free tier only for social layouts | **£0** | Layers, masks, blend modes, PSD, Mac native, no subscription, no platform claim on the work |
| **Generation** | **Codex stills (already paid) + fal.ai pay-per-clip** for Kling v3 Pro, Veo 3.1 only when audio is needed | **~£8 to £15** at 20 five-second Kling clips (20 × $0.56 = $11.20); nothing when idle | List price, no expiring credits, no reseller licence layer, and it already matches the image-routing rule and the approval gate on paid video |
| **Total** | | **£0 fixed; about £10 a month variable** | Compare: CapCut Pro £22 + ImagineArt Ultimate ~£25 to £37 = about **£50 to £60 a month** for less capability and worse licences |

### When the recommendation flips

| Trigger | Change |
|---|---|
| The azatstr-style plugin look (Motion Extractor, Saber, etc.) becomes the signature and cannot be rebuilt in Fusion or TouchDesigner | Add **After Effects single app, £21.98/mo**, keep Resolve for the edit |
| Resolve's free tier hits a wall (Magic Mask for spider isolation, camera tracker for 3D HUD placement) | **Resolve Studio, $295 one-off** (cheaper than 14 months of AE) |
| Clip volume passes roughly 60 Kling clips a month | Price a reseller subscription against fal usage then, not before |
| A client project needs quick vertical social cuts with auto-captions | CapCut **free**, used for that deliverable only, never for unreleased original work |

### In plain English

The three platforms asked about are mostly selling the same generation models at a mark-up, wrapped in an interface. None of them is a compositor, and compositing (HUD over nature, pinned to a moving subject) is the real job. The editor has to accept what TouchDesigner and Blender already make, with transparency intact, and let the overlay track the spider. Resolve does that for free and thinks in nodes the way Dex already does.

Generation is a separate decision and should stay pay-as-you-go until volume proves otherwise. Subscriptions with expiring credits push you to generate for the sake of it; per-clip billing keeps each paid clip a deliberate choice, which is exactly what the existing spend gate is for.

---

## Sources

- InVideo pricing: https://invideo.io/pricing/ ; terms: https://invideo.io/terms-and-conditions/ ; editor: https://invideo.io/make/ai-video-editor/
- ImagineArt pricing (live): https://www.imagine.art/subscription ; plans doc: https://docs.imagine.art/account/subscription-plans.md ; video credits: https://docs.imagine.art/video-tools/video-credits.md ; terms: https://docs.imagine.art/policies/terms-and-conditions.md ; commercial FAQ: https://docs.imagine.art/faq/other-faqs
- CapCut desktop: https://www.capcut.com/tools/desktop-video-editor ; terms (15 Apr 2026): https://www.capcut.com/clause/terms-of-service ; pricing help: https://www.capcut.com/help/how-much-does-capcut-pro-cost ; UK price [3P]: https://marcandrews.com/capcut-pro-price-uk-2026-plans-costs-best-deals/ ; free vs Pro [3P]: https://bigvu.tv/blog/capcut-free-vs-pro-what-2026s-restructure-actually-gives-you/ ; alpha [3P]: https://videoeffectvibe.com/blog/how-to-add-transparent-overlays
- DaVinci Resolve Studio: https://www.blackmagicdesign.com/products/davinciresolve/studio ; Fusion: https://www.blackmagicdesign.com/products/davinciresolve/fusion
- Adobe UK: https://www.adobe.com/uk/products/aftereffects/plans.html ; https://www.adobe.com/uk/products/photoshop/plans.html ; Motion Extractor: https://aescripts.com/motion-extractor/
- Figma: https://www.figma.com/pricing/ ; Affinity: https://www.canva.com/newsroom/news/all-new-affinity/
- fal.ai: https://fal.ai/models/fal-ai/kling-video/v3/pro/image-to-video ; https://fal.ai/models/fal-ai/veo3.1/image-to-video
- Krea: https://www.krea.ai/pricing ; Higgsfield: https://higgsfield.ai/pricing
