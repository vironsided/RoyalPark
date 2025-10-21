# Contributing to RoyalPark

## Development Setup

### Prerequisites
- Node.js v14 or higher
- npm or yarn
- Git

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/RoyalParkJS.git
cd RoyalParkJS
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open your browser:
```
http://localhost:3000/login.html
```

## Project Structure

```
public/
├── admin/          # Admin dashboard pages
├── user/           # User dashboard pages  
├── maintenance/    # Maintenance dashboard pages
├── accountant/     # Accountant dashboard pages
├── css/            # Stylesheets
├── js/             # JavaScript modules
└── images/         # Images and icons
```

## Code Style

- Use consistent indentation (2 spaces)
- Comment your code when necessary
- Follow existing naming conventions
- Keep files organized by feature

## Adding New Features

### Adding a new page:
1. Create HTML file in appropriate role folder
2. Link CSS in `public/css/`
3. Create JavaScript file in `public/js/`
4. Update navigation in sidebar

### Adding translations:
Edit `public/js/i18n.js` and add translations for all 3 languages:
- Russian (ru)
- Azerbaijani (az)
- English (en)

## Testing

Test your changes across:
- Chrome, Firefox, Safari
- Desktop, tablet, mobile views
- Light and dark themes
- All 3 languages

## Git Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "Description of changes"
```

3. Push to GitHub:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request on GitHub

## Questions?

Contact the development team for assistance.

