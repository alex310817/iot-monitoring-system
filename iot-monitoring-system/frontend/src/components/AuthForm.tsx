import { useState } from 'react';
import { useRouter } from 'next/router';
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

interface AuthFormProps {
  isRegister?: boolean;
}

const AuthForm = ({ isRegister = false }: AuthFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useContext(AuthContext)!;
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const endpoint = isRegister ? '/users/register' : '/users/login';
    
    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      if (response.ok) {
        login(data.token);
        router.push('/dashboard');
      } else {
        alert(data.detail || 'Ошибка');
      }
    } catch {
      alert('Ошибка сети');
    }
  };

  return (
    <div>
      <h2>{isRegister ? 'Регистрация' : 'Вход'}</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit">{isRegister ? 'Зарегистрироваться' : 'Войти'}</button>
      </form>
    </div>
  );
};

export default AuthForm;
