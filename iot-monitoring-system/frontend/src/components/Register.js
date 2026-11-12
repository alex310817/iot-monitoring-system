import React, { useState } from 'react';
import { registerUser } from '../services/api';

const Register = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await registerUser(username, password);
            alert('Регистрация успешна! Теперь войдите.');
        } catch (error) {
            console.error(error);
            alert('Ошибка регистрации');
        }
    };

    return (
        <div>
            <h2>Регистрация</h2>
            <form onSubmit={handleSubmit}>
                <input type="text" placeholder="Логин" value={username} onChange={(e) => setUsername(e.target.value)} required />
                <input type="password" placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} required />
                <button type="submit">Зарегистрироваться</button>
            </form>
        </div>
    );
};

export default Register;
