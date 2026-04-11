import React, { useState } from 'react';

function TodoInput({ onAdd, error, inputRef }) {
  const [text, setText] = useState('');

  const handleChange = (e) => {
    setText(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const added = onAdd(text);
    if (added) setText('');
  };

  return (
    <form className="todo-input" onSubmit={handleSubmit} autoComplete="off">
      <input
        ref={inputRef}
        type="text"
        value={text}
        onChange={handleChange}
        placeholder="Введите задачу..."
        aria-label="Текст задачи"
      />
      <button type="submit">Добавить</button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

export default TodoInput;
