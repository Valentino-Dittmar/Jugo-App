window.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('file');
  const canvas    = document.getElementById('canvas');
  const ctx       = canvas.getContext('2d');
  const loupe     = document.getElementById('loupe');
  const tooltip   = document.getElementById('tooltip');
  const swatch    = document.getElementById('swatch');
  const valueEl   = document.getElementById('value');
  const infoBox   = document.getElementById('info');
  const resultBox = document.getElementById('resultBox');
  const resultText= document.getElementById('resultText');
  const likelihoodFill = document.getElementById('likelihoodFill');

  const ZOOM = 3, SIZE = 100;
  let img = null;

  function getCoords(evt) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (evt.clientX - rect.left) * (canvas.width  / rect.width),
      y: (evt.clientY - rect.top)  * (canvas.height / rect.height),
      clientX: evt.clientX,
      clientY: evt.clientY
    };
  }

  function rgbToHex(r,g,b) {
    return '#' + [r,g,b].map(v => v.toString(16).padStart(2,'0')).join('').toUpperCase();
  }

  // Downscale and compress image for API
  function getCompressedB64(dataURL) {
    const imgEl = new Image();
    imgEl.src = dataURL;
    const off = document.createElement('canvas');
    const MAX_DIM = 200;
    const iw = imgEl.width, ih = imgEl.height;
    let w = iw, h = ih;
    if (iw > ih && iw > MAX_DIM) {
      w = MAX_DIM; h = ih * (MAX_DIM / iw);
    } else if (ih > iw && ih > MAX_DIM) {
      h = MAX_DIM; w = iw * (MAX_DIM / ih);
    }
    off.width = w; off.height = h;
    const offCtx = off.getContext('2d');
    offCtx.drawImage(imgEl, 0, 0, w, h);
    // compress quality
    const smallB64 = off.toDataURL('image/jpeg', 0.2);
    return smallB64.split(',')[1];
  }

  // Handle image upload
  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0]; if (!file) return;
    const dataURL = await new Promise(res => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result);
      fr.readAsDataURL(file);
    });
    img = new Image();
    img.src = dataURL;
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height= img.naturalHeight;
      ctx.drawImage(img, 0, 0);
      canvas.style.display = 'block';
      infoBox.style.display = 'none';
      resultBox.style.display = 'none';
      // compress after load
      const compressed = getCompressedB64(dataURL);
      checkCompliance(compressed);
    };
  });

  // Mouse move: loupe + tooltip
  canvas.addEventListener('mousemove', (e) => {
    if (!img) return;
    const {x, y, clientX, clientY} = getCoords(e);
    const [r, g, b] = ctx.getImageData(Math.floor(x), Math.floor(y), 1, 1).data;
    const hex = rgbToHex(r,g,b);

    loupe.style.display = 'block';
    loupe.style.left   = `${clientX}px`;
    loupe.style.top    = `${clientY}px`;
    const bgX = -x*ZOOM + SIZE/2;
    const bgY = -y*ZOOM + SIZE/2;
    loupe.style.backgroundImage = `url(${img.src})`;
    loupe.style.backgroundSize  = `${img.width*ZOOM}px ${img.height*ZOOM}px`;
    loupe.style.backgroundPosition = `${bgX}px ${bgY}px`;

    tooltip.textContent = hex;
    tooltip.style.display = 'block';
    tooltip.style.left    = `${clientX}px`;
    tooltip.style.top     = `${clientY}px`;
  });
  canvas.addEventListener('mouseleave', () => {
    loupe.style.display = 'none';
    tooltip.style.display = 'none';
  });

  // Click: marker + swatch
  canvas.addEventListener('click', (e) => {
    if (!img) return;
    const {x, clientX, clientY} = getCoords(e);
    const rect = canvas.getBoundingClientRect();
    const yPix = (clientY - rect.top) * (canvas.height / rect.height);
    const [r, g, b] = ctx.getImageData(Math.floor(x), Math.floor(yPix), 1, 1).data;
    const hex = rgbToHex(r,g,b);

    let marker = document.querySelector('.marker');
    if (!marker) {
      marker = document.createElement('div');
      marker.className = 'marker';
      document.body.append(marker);
    }
    marker.style.background = hex;
    marker.style.left       = `${clientX}px`;
    marker.style.top        = `${clientY}px`;

    swatch.style.background = hex;
    valueEl.textContent     = hex;
    infoBox.style.display   = 'flex';
  });

  // Server-side compliance check
  async function checkCompliance(imgB64) {
    resultBox.style.display = 'block';
    resultText.textContent  = 'Checking compliance...';
    likelihoodFill.style.width = '0';
    try {
      const res = await fetch('/api/check', {
        method: 'POST',
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ image: imgB64 })
      });
      const json = await res.json();
      if (json.error) throw new Error(json.error);

      resultText.textContent = json.explanation;
      likelihoodFill.style.width = `${Math.min(json.likelihood,100)}%`;
    } catch(err) {
      resultText.textContent = `Error: ${err.message}`;
    }
  }
});