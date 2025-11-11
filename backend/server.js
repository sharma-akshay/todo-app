const express = require('express');
const cors = require('cors');
const todoRoutes = require('./src/routes/todo.routes');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/todos', todoRoutes);

const PORT = 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
