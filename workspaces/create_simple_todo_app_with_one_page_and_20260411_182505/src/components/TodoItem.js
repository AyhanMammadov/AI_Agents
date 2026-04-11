import React from 'react';

function TodoItem({ task, onDelete }) {
  return (
    <li className="todo-item">
      <span className="task-text">{task.text}</span>
      <button className="delete-btn" onClick={() => onDelete(task.id)} aria-label="Удалить задачу">×</button>
    </li>
  );
}

export default TodoItem;
