
# Email Verification Site

A standalone email verification website for CodeCraft Studio users.

## Features

- Clean, responsive design
- Automatic token verification from URL parameters
- Manual token entry option
- Error handling and user feedback
- Mobile-friendly interface

## Deployment

### Netlify
1. Drag and drop this folder to Netlify
2. Site will be automatically deployed
3. Update your Flask app's email template with the Netlify URL

### Vercel
1. Upload this folder to Vercel
2. Deploy as a static site
3. Update your Flask app's email template with the Vercel URL

## Usage

### Automatic Verification
Users receive an email with a link like:
```
https://your-verification-site.netlify.app/?token=abc123xyz
```

### Manual Verification
Users can also manually enter their verification token on the site.

## Configuration

Update the `flaskUrl` in `script.js` to match your Flask app's deployment URL:
```javascript
flaskUrl = 'https://your-flask-app-url.replit.dev';
```

## Files

- `index.html` - Main verification page
- `styles.css` - Styling and responsive design
- `script.js` - Verification logic and API calls
- `README.md` - This documentation
