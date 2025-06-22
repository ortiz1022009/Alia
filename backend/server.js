const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, 'public'))); // para servir login.html, register.html, etc.

// Simulación de base de datos
const users = [];

// Ruta de registro
app.post('/api/register', (req, res) => {
  const { name, email, password } = req.body;
  const userExists = users.find(u => u.email === email);
  if (userExists) {
    return res.status(400).json({ message: 'Usuario ya registrado' });
  }
  users.push({ name, email, password });
  console.log('Usuarios:', users);
  res.status(200).json({ message: 'Usuario creado correctamente' });
});

// Ruta de login
app.post('/api/login', (req, res) => {
  const { email, password } = req.body;
  const user = users.find(u => u.email === email && u.password === password);
  if (!user) {
    return res.status(401).json({ message: 'Credenciales incorrectas' });
  }
  res.status(200).json({ message: 'Inicio de sesión exitoso' });
});

// Ruta para redirigir al dashboard o index.html
app.get('/index.html', (req, res) => {
  res.sendFile(path.join(__dirname, 'public/index.html'));
});

app.listen(PORT, () => {
  console.log(`Servidor iniciado en http://localhost:${PORT}`);
});
