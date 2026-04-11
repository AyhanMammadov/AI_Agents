import React, { useState, useEffect, useRef } from 'react';
import TodoInput from './components/TodoInput';
import TodoList from './components/TodoList';
import { loadTasks, saveTasks } from './utils/storage';
import './styles.css';

function App() {
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    const stored = loadTasks();
    if (stored) setTasks(stored);
  }, []);

  useEffect(() => {
    saveTasks(tasks);
  }, [tasks]);

  const handleAddTask = (text) => {
    if (!text.trim()) {
      setError('Текст задачи не может быть пустым');
      return false;
    }
    const newTask = { id: Date.now().toString(), text };
    setTasks([...tasks, newTask]);
    setError('');
    if (inputRef.current) inputRef.current.focus();
    return true;
  };

  const handleDeleteTask = (id) => {
    setTasks(tasks.filter((t) => t.id !== id));
  };

  return (
    <div className="todo-app">
      <h1>TODO</h1>
      <TodoInput onAdd={handleAddTask} error={error} inputRef={inputRef} />
      <TodoList tasks={tasks} onDelete={handleDeleteTask} />
    </div>
  );
}

export default App;
