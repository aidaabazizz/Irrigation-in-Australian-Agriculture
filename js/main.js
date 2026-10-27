// Renders every <div class="vis" data-spec="..."> with vega-embed.
// Waits for web fonts first so chart titles and labels use them.
const ready = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
ready.then(() => {
  document.querySelectorAll('.vis[data-spec]').forEach(el => {
    vegaEmbed(el, 'specs/' + el.dataset.spec + '.vl.json', {actions: false})
      .catch(e => { el.textContent = 'Chart failed to load: ' + e; });
  });
});
