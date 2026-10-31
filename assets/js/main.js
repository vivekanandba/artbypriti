// Project override of themes/gallery/assets/js/main.js (spec 016-lightbox).
//
// Two of the theme's five modules are dropped, because both key off `#gallery` and this site
// has no such element on any page -- measured, not assumed:
//
//   gallery.js   justified grid layout. The home page uses the theme's album-card.html, so the
//                branch that renders #gallery never renders. Dead code, and actively harmful if
//                #gallery is ever added for another purpose: it absolutely-positions every
//                .gallery-item into a 288px row.
//   lightbox.js  same guard, so the lightbox never initialised anywhere. Replaced by
//                artwork-lightbox.js, which scopes itself to the artwork page's own section.
//
// The theme is vendored and deliberately not edited (Constitution IX); Hugo resolves this file
// ahead of the theme's copy. Keep it in step with themes/gallery/UPSTREAM.md when the theme is
// updated -- if upstream adds a module here, it will not appear on this site until it is added
// to this list.
import "./menu.js";
import "./lazysizes.js";
import "./artwork-lightbox.js";
import "./custom.js";
