"""Browser-side recorder: every DOM change and every request WebFlow makes while a step runs.

Installed idempotently (a page reload wipes it, so it is installed again at the start of each step)
and drained when the step ends."""

INSTALL_SCRIPT = r"""
if (window.__autohubRec) { return true; }
const rec = { events: [], dropped: 0, t0: performance.now() };
const push = (e) => {
  if (rec.events.length >= 3000) { rec.dropped++; return; }
  e.t = Math.round(performance.now() - rec.t0);
  rec.events.push(e);
};
const cut = (v, n) => (v === null || v === undefined) ? null : String(v).slice(0, n || 120);
const path = (el) => {
  const parts = [];
  for (; el && el.nodeType === 1 && parts.length < 6; el = el.parentElement) {
    let p = el.tagName.toLowerCase();
    if (el.id) { parts.unshift(p + '#' + el.id); break; }
    const same = el.parentElement ? [...el.parentElement.children].filter(c => c.tagName === el.tagName) : [];
    if (same.length > 1) p += ':nth-of-type(' + (same.indexOf(el) + 1) + ')';
    parts.unshift(p);
  }
  return parts.join(' > ');
};
const describe = (n) => n.nodeType === 1
  ? { tag: n.tagName.toLowerCase(), id: n.id || null, class: cut(n.getAttribute('class')), label: cut(n.getAttribute('aria-label')), text: cut((n.innerText || '').trim(), 80) }
  : { text: cut((n.textContent || '').trim(), 80) };
new MutationObserver((mutations) => {
  for (const m of mutations) {
    if (m.type === 'childList') {
      const where = path(m.target);
      m.addedNodes.forEach(n => push({ type: 'added', in: where, node: describe(n) }));
      m.removedNodes.forEach(n => push({ type: 'removed', in: where, node: describe(n) }));
    } else if (m.type === 'attributes') {
      push({ type: 'attr', target: path(m.target), attr: m.attributeName, old: cut(m.oldValue), new: cut(m.target.getAttribute(m.attributeName)) });
    } else if (m.type === 'characterData') {
      push({ type: 'text', target: path(m.target.parentElement), old: cut(m.oldValue), new: cut(m.target.data) });
    }
  }
}).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeOldValue: true, characterData: true, characterDataOldValue: true });

const realFetch = window.fetch;
if (realFetch) {
  window.fetch = function (input, init) {
    const started = performance.now();
    const method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
    const url = cut(input && input.url ? input.url : input, 300);
    return realFetch.apply(this, arguments).then(
      (r) => { push({ type: 'request', api: 'fetch', method, url, status: r.status, ms: Math.round(performance.now() - started) }); return r; },
      (e) => { push({ type: 'request', api: 'fetch', method, url, status: 'failed', error: cut(e), ms: Math.round(performance.now() - started) }); throw e; });
  };
}
const realOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url) {
  const started = performance.now();
  this.addEventListener('loadend', () => push({ type: 'request', api: 'xhr', method: String(method).toUpperCase(), url: cut(url, 300), status: this.status, ms: Math.round(performance.now() - started) }));
  return realOpen.apply(this, arguments);
};
rec.drain = () => { const out = { events: rec.events, dropped: rec.dropped }; rec.events = []; rec.dropped = 0; return out; };
window.__autohubRec = rec;
return true;
"""

#: ``null`` when the recorder is gone, i.e. the page was reloaded during the step.
DRAIN_SCRIPT = "return window.__autohubRec ? window.__autohubRec.drain() : null;"
