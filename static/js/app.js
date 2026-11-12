(function () {
  "use strict";
  var L = "A-Za-zÀ-ÖØ-öø-ÿŒœ";
  var RULES = {
    line: new RegExp("[^" + L + "0-9 ]", "g"),
    multi: new RegExp("[^" + L + "0-9 \\n]", "g"),
    phone: /[^0-9+ ]/g,
    email: /[^A-Za-z0-9@._-]/g
  };

  // Filtre en direct : les caractères interdits ne peuvent pas être saisis ni collés.
  document.addEventListener("input", function (e) {
    var el = e.target, kind = el.getAttribute && el.getAttribute("data-safe");
    if (!kind || !RULES[kind]) return;
    var clean = el.value.replace(RULES[kind], "");
    if (clean !== el.value) {
      el.value = clean;
      el.classList.add("ring-2", "ring-red-300");
      setTimeout(function () { el.classList.remove("ring-2", "ring-red-300"); }, 700);
    }
  });

  function csrf() {
    var m = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  // Menu mobile
  var btn = document.getElementById("menu-btn"), menu = document.getElementById("menu");
  if (btn && menu) btn.addEventListener("click", function () {
    var open = menu.classList.toggle("hidden") === false;
    btn.setAttribute("aria-expanded", open);
  });

  // Messages qui disparaissent
  document.querySelectorAll("[data-toast]").forEach(function (t) {
    setTimeout(function () { t.style.transition = "opacity .5s"; t.style.opacity = "0"; setTimeout(function () { t.remove(); }, 500); }, 6000);
  });

  // Animation d'apparition
  var items = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("in"); io.unobserve(x.target); } });
    }, { threshold: 0.1 });
    items.forEach(function (i) { io.observe(i); });
  } else items.forEach(function (i) { i.classList.add("in"); });

  // Inscription : champs soudeur affichés seulement si besoin
  var roleInputs = document.querySelectorAll("input[name=role]");
  if (roleInputs.length) {
    var artisanFields = ["business_name", "city", "location", "whatsapp"];
    var sync = function () {
      var r = document.querySelector("input[name=role]:checked");
      var show = r && r.value === "artisan";
      artisanFields.forEach(function (n) {
        var w = document.querySelector('[data-field="' + n + '"]');
        if (w) w.style.display = show ? "" : "none";
      });
    };
    roleInputs.forEach(function (r) { r.addEventListener("change", sync); });
    sync();
  }

  // Recherche dynamique sans rechargement
  var results = document.getElementById("results"), form = document.getElementById("filters");
  if (results && form) {
    var timer;
    var run = function () {
      var params = new URLSearchParams(new FormData(form));
      fetch(results.dataset.api + "?" + params.toString(), { headers: { Accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          results.replaceChildren();
          document.getElementById("count").textContent = d.results.length + " résultat" + (d.results.length > 1 ? "s" : "");
          if (!d.results.length) { results.appendChild(el("p", "text-slate-500", "Aucun soudeur ne correspond.")); return; }
          d.results.forEach(function (a) {
            var c = el("article", "card-hover rounded-2xl bg-white p-5 shadow-sm");
            c.appendChild(el("h3", "font-bold text-lg", a.name + (a.verified ? " ✔" : "")));
            c.appendChild(el("p", "text-sm text-slate-500 mt-1", a.location + ", " + a.city));
            c.appendChild(el("p", "text-sm text-slate-600 mt-2", a.services + " service(s)"));
            var l = el("a", "mt-4 inline-block rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white", "Voir la fiche");
            l.href = "/soudeurs/" + parseInt(a.id, 10) + "/";
            c.appendChild(l); results.appendChild(c);
          });
        }).catch(function () {});
    };
    form.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(run, 300); });
    form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  }

  // Bouton Contacter : le numéro WhatsApp n'est renvoyé qu'au clic
  var cb = document.getElementById("contact-btn");
  if (cb) cb.addEventListener("click", function () {
    cb.disabled = true;
    fetch(cb.dataset.url, { method: "POST", headers: { "X-CSRFToken": csrf() }, credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        var p = document.getElementById("contact-phone");
        p.textContent = "Tél : +" + d.phone; p.classList.remove("hidden");
        if (/^https:\/\/wa\.me\/[0-9]+/.test(d.url)) { if (window.Capacitor) window.location.href = d.url; else window.open(d.url, "_blank", "noopener"); }
      }).catch(function () { cb.textContent = "Réessayez dans un instant"; })
      .finally(function () { setTimeout(function () { cb.disabled = false; }, 1500); });
  });

  // Attente de la confirmation du paiement
  var ps = document.getElementById("pay-state");
  if (ps) {
    var n = 0, t = setInterval(function () {
      fetch(ps.dataset.url, { credentials: "same-origin" }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.status === "success") { clearInterval(t); ps.textContent = "Paiement confirmé !"; setTimeout(function () { location.href = ps.dataset.next; }, 1200); }
        else if (d.status === "failed") { clearInterval(t); ps.textContent = "Paiement refusé ou annulé."; }
      }).catch(function () {});
      if (++n > 60) { clearInterval(t); ps.textContent = "Délai dépassé. Vérifiez votre espace plus tard."; }
    }, 4000);
  }
})();
