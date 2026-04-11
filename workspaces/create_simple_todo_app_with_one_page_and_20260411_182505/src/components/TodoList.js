import React from 'react';
import TodoItem from './TodoItem';

function TodoList({ tasks, onDelete }) {
  if (!tasks.length) {
    return <div className="empty">Нет задач</div>;
  }
  return (
    <ul className="todo-list">
      {tasks.map((task) => (
        <TodoItem key={task.id} task={task} onDelete={onDelete} />
      ))}
    </ul>
  );
}

export default TodoList;
