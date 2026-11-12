import { useTheme } from '../context/ThemeContext';  // Импортируем хук из контекста

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();  // Получаем текущую тему и функцию для переключения

  return (
    <button onClick={toggleTheme}>
      {theme === 'light' ? '🌙 Темная тема' : '☀️ Светлая тема'}
    </button>
  );
};

export default ThemeToggle;
