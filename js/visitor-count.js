(function() {
  document.querySelectorAll('.build-id[data-build-id]').forEach(function(el) {
    var ts = parseInt(el.getAttribute('data-build-id'), 10) * 1000;
    var d = new Date(ts);
    var pad = function(n) { return n < 10 ? '0' + n : n; };
    var offset = -d.getTimezoneOffset();
    var sign = offset >= 0 ? '+' : '-';
    var oh = pad(Math.floor(Math.abs(offset) / 60));
    var om = pad(Math.abs(offset) % 60);
    el.title = d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) +
      'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()) +
      sign + oh + ':' + om;
  });
  document.querySelectorAll('.build-id[data-gc-path]').forEach(function(el) {
    var path = el.getAttribute('data-gc-path');
    var span = el.querySelector('.views');
    if (!span) return;
    var r = new XMLHttpRequest();
    r.addEventListener('load', function() {
      if (r.status === 200) {
          var count = JSON.parse(r.responseText).count;
          span.textContent = count;
          span.title = count + ' views';
        } else {
          span.textContent = '--';
          span.title = '';
        }
    });
    r.open('GET', 'https://covenantbiblicist.goatcounter.com/counter' + path + '.json');
    r.send();
  });
})();
