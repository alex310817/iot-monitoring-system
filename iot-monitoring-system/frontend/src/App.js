import React, { useState } from 'react';
import Register from './components/Register';
import Login from './components/Login';
import DeviceControl from './components/DeviceControl';

const App = () => {
    const [token, setToken] = useState(localStorage.getItem('token'));

    return (
        <div>
            {!token ? (
                <div>
                    <Register />
                    <Login setToken={setToken} />
                </div>
            ) : (
                <DeviceControl />
            )}
        </div>
    );
};

export default App;
