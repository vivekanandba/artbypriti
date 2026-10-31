// Open a painting in a lightbox instead of navigating away to a bare JPEG.
//
// WHY THIS EXISTS AND THE THEME'S VERSION DOES NOT WORK (spec 016).
//
// themes/gallery/assets/js/lightbox.js initialises only `if (document.getElementById(
// "gallery"))`. That #gallery div lives in the LISTING branch of layouts/partials/gallery.html
// -- the branch that never renders on this site, because the home page uses the theme's
// home.html -> album-card.html. Measured: 0 pages contained #gallery, 0 PhotoSwipe roots were
// ever created, and clicking a painting navigated to the raw JPEG. ~94KB of JS shipped to every
// visitor and never ran (docs/incidents.md #11).
//
// The obvious fix -- put id="gallery" on the artwork wrapper -- was tried and MEASURED, and it
// is wrong: themes/gallery/assets/js/gallery.js keys off the same id and unconditionally
// absolutely-positions every .gallery-item into a 288px justified row. On a single-painting page
// that is a layout regression, and it failed five screenshot baselines. The id is overloaded:
// it means "lightbox root" AND "justified grid root", and this page wants only the first.
//
// So the root is the artwork section instead, and this module replaces the theme's lightbox.js
// and gallery.js in assets/js/main.js (a project override; the theme itself is vendored and not
// edited -- Constitution IX). PhotoSwipe is imported from the theme rather than copied, so it is
// still bundled exactly once.
import PhotoSwipeLightbox from "./photoswipe/photoswipe-lightbox.esm.js";
import PhotoSwipe from "./photoswipe/photoswipe.esm.js";
import PhotoSwipeDynamicCaption from "./photoswipe/photoswipe-dynamic-caption-plugin.esm.min.js";
import * as params from "@params";

const gallery = document.querySelector(".gallery-single-centered");

if (gallery && gallery.querySelector(".gallery-item")) {
  const lightbox = new PhotoSwipeLightbox({
    gallery,
    children: ".gallery-item",
    showHideAnimationType: "zoom",
    bgOpacity: 1,
    pswpModule: PhotoSwipe,
    // Clicking the enlarged image closes it again, which is what a visitor expects when the
    // image is the only thing on screen.
    imageClickAction: "close",
    closeTitle: params.closeTitle,
    zoomTitle: params.zoomTitle,
    arrowPrevTitle: params.arrowPrevTitle,
    arrowNextTitle: params.arrowNextTitle,
    errorMsg: params.errorMsg,
  });

  // Before this, clicking a painting navigated to the 1600px variant, so the visitor could save
  // it. The lightbox intercepts that click, so the download button preserves the capability
  // rather than quietly removing it. It points at the anchor's href -- the derived variant,
  // never the full-resolution master, which is not published at all (spec 000).
  lightbox.on("uiRegister", () => {
    lightbox.pswp.ui.registerElement({
      name: "download-button",
      order: 8,
      isButton: true,
      tagName: "a",
      html: {
        isCustomSVG: true,
        inner:
          '<path d="M20.5 14.3 17.1 18V10h-2.2v7.9l-3.4-3.6L10 16l6 6.1 6-6.1ZM23 23H9v2h14Z" id="pswp__icn-download"/>',
        outlineID: "pswp__icn-download",
      },
      onInit: (el, pswp) => {
        el.setAttribute("download", "");
        el.setAttribute("target", "_blank");
        el.setAttribute("rel", "noopener");
        el.setAttribute("title", params.downloadTitle || "Download");
        pswp.on("change", () => {
          el.href = pswp.currSlide.data.element.href;
        });
      },
    });
  });

  // The caption carries the painting's dimensions, from data-pswp-caption.
  new PhotoSwipeDynamicCaption(lightbox, {
    mobileLayoutBreakpoint: 700,
    type: "auto",
    mobileCaptionOverlapRatio: 1,
  });

  lightbox.init();
}
