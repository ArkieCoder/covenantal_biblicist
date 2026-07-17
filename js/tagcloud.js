var tagAngles = [0, 90, 180, 270];
var tagColors = [
  '#2c3539', '#3d4f5c', '#4a5d6b', '#566b79',
  '#637a88', '#1a1a2e', '#2a3a4a', '#3a4a5a'
];

function renderTagCloud(tagData) {
  if (!tagData || tagData.length === 0) return;
  var container = document.getElementById('tag-cloud');
  var maxCount = Math.max.apply(null, tagData.map(function(t) { return t.count; }));
  var minCount = Math.min.apply(null, tagData.map(function(t) { return t.count; }));
  var minSize = 1.0;
  var maxSize = 2.6;
  var STEP = 1;
  var GAP = 0;

  function overlaps(a, b) {
    return a.x - GAP < b.x + b.w && a.x + a.w + GAP > b.x &&
           a.y - GAP < b.y + b.h && a.y + a.h + GAP > b.y;
  }

  var placed = [];
  var items = tagData.map(function(tag, i) {
    var fontSize;
    if (maxCount === minCount) {
      fontSize = (minSize + maxSize) / 2;
    } else {
      fontSize = minSize + (maxSize - minSize) * (tag.count - minCount) / (maxCount - minCount);
    }
    return {
      tag: tag,
      fontSize: fontSize,
      angle: tagAngles[i % tagAngles.length],
      color: tagColors[i % tagColors.length]
    };
  });

  items.sort(function(a, b) { return b.fontSize - a.fontSize; });

  container.style.position = 'relative';
  container.style.minHeight = '200px';

  items.forEach(function(item) {
    var a = document.createElement('a');
    a.href = 'tags/' + item.tag.name.replace(/ /g, '-').toLowerCase() + '/';
    a.textContent = item.tag.name;
    a.className = 'tag-cloud-link';
    a.style.fontSize = item.fontSize.toFixed(2) + 'rem';
    a.style.color = item.color;
    a.style.position = 'absolute';
    a.style.whiteSpace = 'nowrap';
    container.appendChild(a);

    var lw = a.offsetWidth;
    var lh = a.offsetHeight;

    a.style.transform = 'rotate(' + item.angle + 'deg)';

    var vw, vh;
    if (item.angle === 90 || item.angle === 270) {
      vw = lh; vh = lw;
    } else {
      vw = lw; vh = lh;
    }

    var cx = container.offsetWidth / 2 - vw / 2;
    var cy = container.offsetHeight / 2 - vh / 2;
    var found = false;
    var maxW = container.offsetWidth;

    for (var r = 0; r < 1000 && !found; r++) {
      var steps = Math.max(20, Math.floor(2 * Math.PI * r * 5 / Math.max(vw, vh)));
      for (var s = 0; s < steps && !found; s++) {
        var theta = (2 * Math.PI * s) / steps;
        var tx = cx + r * STEP * Math.cos(theta);
        var ty = cy + r * STEP * Math.sin(theta);

        if (tx < -2 || tx + vw > maxW + 2) continue;

        var candidate = { x: tx, y: ty, w: vw, h: vh };
        var collision = false;
        for (var p = 0; p < placed.length; p++) {
          if (overlaps(candidate, placed[p].vb)) {
            collision = true;
            break;
          }
        }

        if (!collision) {
          var cssX, cssY;
          if (item.angle === 90 || item.angle === 270) {
            var d = (lw - lh) / 2;
            cssX = tx - d;
            cssY = ty + d;
          } else {
            cssX = tx;
            cssY = ty;
          }

          a.style.left = cssX + 'px';
          a.style.top = cssY + 'px';
          placed.push({ el: a, vb: candidate });
          found = true;
        }
      }
    }
  });

  if (placed.length > 0) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    placed.forEach(function(p) {
      var v = p.vb;
      if (v.x < minX) minX = v.x;
      if (v.y < minY) minY = v.y;
      if (v.x + v.w > maxX) maxX = v.x + v.w;
      if (v.y + v.h > maxY) maxY = v.y + v.h;
    });
    var cloudW = maxX - minX;
    var cloudH = maxY - minY;
    var pad = 8;
    container.style.height = (cloudH + pad * 2) + 'px';
    var shiftX = (container.offsetWidth - cloudW) / 2 - minX;
    var shiftY = pad - minY;
    placed.forEach(function(p) {
      var el = p.el;
      el.style.left = (parseFloat(el.style.left) + shiftX) + 'px';
      el.style.top = (parseFloat(el.style.top) + shiftY) + 'px';
    });
  }
}
