# 🏢 RoyalPark - Utility Management System

Modern web application for managing residential complex utilities with multi-role support.

![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)
![Express](https://img.shields.io/badge/Express.js-404D59?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

## ✨ Features

- 🎨 **Modern UI/UX** - Beautiful gradient designs with smooth animations
- 🌓 **Dark/Light Theme** - Automatic theme switching with preference saving
- 🌍 **Multi-language** - Support for Russian, Azerbaijani, and English
- 👥 **Multi-role System** - 4 different user roles with unique dashboards
- 📊 **Interactive Charts** - Real-time data visualization with Chart.js
- 📱 **Responsive Design** - Works perfectly on desktop, tablet, and mobile
- ⚡ **Fast & Lightweight** - Optimized performance with vanilla JavaScript

## 🚀 Quick Start

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/RoyalParkJS.git

# Navigate to project directory
cd RoyalParkJS

# Install dependencies
npm install

# Start the server
npm start
```

The application will be available at `http://localhost:3000`

## 📱 User Roles

### 🏢 Administrator
Full system access with management capabilities:
- User management
- Building and apartment management
- Payment and invoice tracking
- Repair request oversight
- System analytics and reports

**Access:** `http://localhost:3000/admin/dashboard.html`

### 👤 Resident (User)
Personal dashboard for apartment owners:
- View and pay utility bills
- Submit repair requests
- Track payment history
- View announcements and news

**Access:** `http://localhost:3000/user/dashboard.html`

### 🔧 Maintenance Service
Service team dashboard:
- Manage repair requests
- Verify meter readings
- Track work progress
- Update task statuses

**Access:** `http://localhost:3000/maintenance/dashboard.html`

### 💰 Accountant
Financial management dashboard:
- Payment processing
- Invoice generation
- Financial reports
- Debt tracking
- Revenue analytics

**Access:** `http://localhost:3000/accountant/dashboard.html`

## 🎨 Color Scheme

Each role has a unique gradient theme:

- **Admin**: Purple gradient (#667eea → #764ba2)
- **User**: Blue gradient (#4facfe → #00f2fe)
- **Maintenance**: Orange gradient (#fa709a → #fee140)
- **Accountant**: Green gradient (#11998e → #38ef7d)

## 🌍 Supported Languages

- 🇷🇺 Russian (Русский)
- 🇦🇿 Azerbaijani (Azərbaycan)
- 🇬🇧 English

Switch languages using the language selector in the top navigation bar.

## 🛠️ Technology Stack

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap 5
- Chart.js for data visualization
- Animate.css for animations

### Backend
- Node.js
- Express.js
- dotenv for environment variables

## 📁 Project Structure

```
RoyalParkJS/
├── public/
│   ├── admin/              # Admin panel pages
│   ├── user/               # User panel pages
│   ├── maintenance/        # Maintenance panel pages
│   ├── accountant/         # Accountant panel pages
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── images/             # Images and icons
│   └── login.html          # Login page
├── server.js               # Express server
├── package.json            # Project dependencies
└── README.md               # This file
```

## 🔐 Development Mode

For development purposes, authentication is currently disabled. You can access any dashboard directly.

To enable authentication, modify the `checkAuth()` function in respective JavaScript files.

## 🌓 Theme Switching

The application supports automatic dark/light theme switching:

- Click the theme toggle button (🌓) in the top navigation
- Theme preference is saved in localStorage
- Smooth transitions between themes

## 📊 Key Features

### Dashboard Statistics
- Real-time data updates
- Interactive charts
- Quick action buttons
- Recent activity feed

### Payment Management
- Payment filtering by date, status, method
- Export to Excel/PDF
- Payment history tracking

### Meter Verification
- Automatic anomaly detection
- Consumption calculation
- Approval/rejection workflow

### Responsive Design
- Mobile-first approach
- Breakpoints: 320px, 768px, 1024px, 1920px
- Touch-friendly interface

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
PORT=3000
NODE_ENV=development
```

## 📝 Scripts

```bash
# Start server
npm start

# Development mode with auto-reload
npm run dev
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is proprietary software. © 2024 RoyalPark. All rights reserved.

## 📧 Contact

For questions or support, please contact the development team.

---

**Made with ❤️ for RoyalPark Baku**

