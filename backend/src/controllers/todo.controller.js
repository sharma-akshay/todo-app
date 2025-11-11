let todos = [];

exports.getTodos = (req, res) => res.json(todos);

exports.addTodo = (req, res) => {
  const { text } = req.body;
  const newTodo = { id: Date.now(), text, completed: false };
  todos.push(newTodo);
  res.json(newTodo);
};

exports.updateTodo = (req, res) => {
  const { id } = req.params;
  const { completed } = req.body;
  todos = todos.map(t => t.id == id ? { ...t, completed } : t);
  res.json({ message: "Updated" });
};

exports.deleteTodo = (req, res) => {
  const { id } = req.params;
  todos = todos.filter(t => t.id != id);
  res.json({ message: "Deleted" });
};
