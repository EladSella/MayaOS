const https = require('https');
const fs = require('fs');
const path = require('path');

const payload = JSON.stringify({
  packageId: "com.mayaos.app",
  name: "MayaOS",
  launchUrl: "https://mayaos.onrender.com",
  themeColor: "#0a0f1e",
  backgroundColor: "#060c1a",
  startUrl: "/",
  iconUrl: "https://mayaos.onrender.com/icon-512.png",
  manifestUrl: "https://mayaos.onrender.com/manifest.json",
  signingMode: "none",
  rotationAllowed: false,
  display: "standalone",
  orientation: "portrait",
  shortcuts: [],
  features: { locationDelegation: { enabled: false }, playBilling: { enabled: false } },
  isChromeOSOnly: false,
  enableNotifications: false,
  enableSiteSettingsShortcut: true,
  enableDex: true,
  splashScreenFadeOutDuration: 300,
  fallbackType: "customtabs",
  webManifestUrl: "https://mayaos.onrender.com/manifest.json"
});

console.log('Calling PWABuilder API...');

const options = {
  hostname: 'pwabuilder-apk.dl.azure.websites.net',
  port: 443,
  path: '/generateApkZip',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(payload)
  }
};

const req = https.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  if (res.statusCode === 200) {
    const chunks = [];
    res.on('data', (chunk) => chunks.push(chunk));
    res.on('end', () => {
      const buf = Buffer.concat(chunks);
      const outPath = path.join(__dirname, 'mayaos.zip');
      fs.writeFileSync(outPath, buf);
      console.log(`SUCCESS! Saved to: ${outPath} (${buf.length} bytes)`);
    });
  } else {
    let body = '';
    res.on('data', d => body += d);
    res.on('end', () => console.log('Response:', body.substring(0, 500)));
  }
});

req.on('error', (e) => console.error('Error:', e.message));
req.setTimeout(60000, () => { console.log('Timeout'); req.destroy(); });
req.write(payload);
req.end();
