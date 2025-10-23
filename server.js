const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/css', express.static(path.join(__dirname, 'public/css')));
app.use('/js', express.static(path.join(__dirname, 'public/js')));
app.use('/assets', express.static(path.join(__dirname, 'public/assets')));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// Admin Panel - SPA Routing
// Все маршруты /admin/* перенаправляются на index.html для клиентской маршрутизации
app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'admin', 'index.html'));
});

app.get('/admin/*', (req, res) => {
    // Проверяем, не запрашивается ли файл контента напрямую
    if (req.path.includes('/admin/content/')) {
        // Позволяем запросы к файлам контента для AJAX загрузки
        res.sendFile(path.join(__dirname, 'public', req.path));
    } else {
        // Все остальные маршруты перенаправляем на index.html для SPA
        res.sendFile(path.join(__dirname, 'public', 'admin', 'index.html'));
    }
});

app.get('/user', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'user', 'dashboard.html'));
});

app.get('/maintenance', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'maintenance', 'dashboard.html'));
});

app.get('/accountant', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'accountant', 'dashboard.html'));
});

// API Routes (будут подключаться к FastAPI backend)
app.post('/api/login', (req, res) => {
    // Временная заглушка - будет подключено к FastAPI
    const { username, password, role } = req.body;
    
    // Здесь будет запрос к FastAPI backend
    res.json({
        success: true,
        role: role,
        token: 'temporary_token',
        message: 'Login successful'
    });
});

app.listen(PORT, () => {
    console.log(`🚀 RoyalPark Frontend Server running on port ${PORT}`);
    console.log(`📱 Access the application at: http://localhost:${PORT}`);
});

