# Vendored typefaces

Two open-licence faces, chosen to sit in the same register as the reference
this project is aimed at (explore.ownprimland.com, which uses Inferi and
Centra — both commercial, neither redistributable):

| file | family | licence |
|---|---|---|
| `CormorantGaramond-300.woff2`, `-400`, `-300i` | Cormorant Garamond, by Christian Thalmann (Catharsis Fonts) | SIL Open Font Licence 1.1 |
| `Jost-300.woff2`, `-400`, `-500` | Jost*, by Owen Earl (indestructible type*) | SIL Open Font Licence 1.1 |

Latin subsets only, taken from the Google Fonts CDN and vendored rather than
linked so the map renders identically offline. That is not a preference: the
descent capture runs against a local server, and a webfont that arrives late
— or not at all — would change what is on screen between one run and the next.
