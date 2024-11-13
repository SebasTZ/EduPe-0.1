const express = require('express');
const mysql = require('mysql2');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const path = require('path');
const cookieParser = require('cookie-parser');
const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());  // Agregar cookie-parser para manejar cookies
app.use(express.static(path.join(__dirname, '../public')));

// Conexión a la base de datos MySQL
const db = mysql.createConnection({
    host: 'localhost',        // Host es localhost
    user: 'root',             // Usuario root
    password: 'Sebas3120',             // Contraseña vacía, ya que indicaste que no tiene
    database: 'chatter_ai_db' // Nombre de la base de datos que has creado
});

db.connect((err) => {
    if (err) {
        console.error('Error al conectar con MySQL:', err);
        return;
    }
    console.log('Conectado a MySQL');
});

// Ruta para servir el formulario de login
app.get('/login', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/login.html'));
});

// Ruta para servir el formulario de registro
app.get('/register', (req, res) => {
    res.sendFile(path.join(__dirname, '../views/register.html'));
});

// Ruta de Registro
app.post('/register', async (req, res) => {
    const { nombre, email, password } = req.body;

    // Verificar si el usuario ya está registrado
    db.query('SELECT * FROM users WHERE email = ?', [email], async (error, results) => {
        if (error) {
            return res.status(500).json({ message: 'Error en el servidor' });
        }
        if (results.length > 0) {
            return res.status(400).json({ message: 'El usuario ya está registrado' });
        }

        // Hashear la contraseña
        let hashedPassword = await bcrypt.hash(password, 10);

        db.query('INSERT INTO users SET ?', { nombre, email, password: hashedPassword }, (error, results) => {
            if (error) {
                return res.status(500).json({ message: 'Error al registrar el usuario' });
            }
            res.redirect('/login');
        });
    });
});

// Ruta de Login
app.post('/login', (req, res) => {
    const { email, password } = req.body;

    db.query('SELECT * FROM users WHERE email = ?', [email], async (error, results) => {
        if (error) {
            return res.status(500).json({ message: 'Error en el servidor' });
        }
        if (results.length === 0) {
            return res.status(404).json({ message: 'Usuario no encontrado' });
        }

        const user = results[0];
        const isPasswordValid = await bcrypt.compare(password, user.password);

        if (!isPasswordValid) {
            return res.status(401).json({ message: 'Contraseña incorrecta' });
        }

        const token = jwt.sign({ id: user.id }, 'secretkey', { expiresIn: '1h' });
        res.cookie('token', token, { httpOnly: true }).redirect('/');
    });
});

// Ruta para el chat IA (si el usuario está autenticado)
app.get('/', (req, res) => {
    const token = req.cookies.token;
    if (!token) {
        return res.redirect('/login');
    }

    jwt.verify(token, 'secretkey', (err, decoded) => {
        if (err) {
            return res.clearCookie('token').redirect('/login');
        }
        res.sendFile(path.join(__dirname, '../views/index.html'));
    });
});

// Ruta para cerrar sesión
app.get('/logout', (req, res) => {
    res.clearCookie('token');
    res.redirect('/login');
});

// Iniciar el servidor
app.listen(5000, () => {
    console.log('Servidor corriendo en el puerto 5000');
});

