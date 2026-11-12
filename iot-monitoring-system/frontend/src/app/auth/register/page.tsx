'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { 
  TextField, 
  Button, 
  Typography, 
  Alert,
  Container,
  Box,
  Paper,
  CircularProgress,
  Link,
  IconButton,
  InputAdornment
} from '@mui/material';
import { Visibility, VisibilityOff, Email, Person, Lock, ArrowBack } from '@mui/icons-material';
import { useThemeMode } from '../../providers';

export default function Register() {
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();
  const { darkMode } = useThemeMode();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (step === 1) {
        const response = await fetch('http://localhost:8000/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });

        const data = await response.json();
        
        if (response.ok) {
          setStep(2);
        } else {
          throw new Error(data.detail || 'Ошибка регистрации');
        }
      } else {
        if (verificationCode.length !== 4) {
          setError('Код подтверждения должен состоять из 4 цифр');
          return;
        }

        const response = await fetch('http://localhost:8000/auth/verify-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            code: verificationCode
          }),
        });

        const data = await response.json();
        
        if (response.ok) {
          // Сохраняем токен и перенаправляем на дашборд
          localStorage.setItem('token', data.access_token);
          router.push('/dashboard');
        } else {
          throw new Error(data.detail || 'Неверный код подтверждения');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        backgroundImage: 'url(/images/background.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
        }
      }}
    >
      <Container component="main" maxWidth="xs">
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative'
          }}
        >
          <IconButton 
            onClick={() => router.push('/')}
            sx={{ 
              position: 'absolute',
              top: 20,
              left: 0,
              color: darkMode ? 'white' : 'inherit'
            }}
          >
            <ArrowBack />
          </IconButton>
          <Paper 
            elevation={6}
            sx={{
              p: 4,
              width: '100%',
              borderRadius: 2,
              background: darkMode ? 'rgba(30, 30, 30, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(10px)',
              color: darkMode ? '#fff' : 'inherit',
            }}
          >
            <Typography
              component="h1"
              variant="h4"
              sx={{
                mb: 3,
                fontWeight: 600,
                textAlign: 'center',
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                color: 'transparent',
              }}
            >
              {step === 1 ? 'Регистрация' : 'Подтверждение'}
            </Typography>

            {error && (
              <Alert 
                severity="error"
                variant="filled"
                sx={{ mb: 2, borderRadius: 2 }}
              >
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              {step === 1 ? (
                <>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="username"
                    label="Имя пользователя"
                    name="username"
                    autoComplete="username"
                    autoFocus
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Person color="primary" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: darkMode ? 'rgba(255,255,255,0.7)' : undefined,
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.23)' : undefined,
                        },
                        '&:hover fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.4)' : undefined,
                        },
                        '& input': {
                          color: darkMode ? '#fff' : undefined,
                        }
                      }
                    }}
                  />
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    id="email"
                    label="Email"
                    name="email"
                    autoComplete="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Email color="primary" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: darkMode ? 'rgba(255,255,255,0.7)' : undefined,
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.23)' : undefined,
                        },
                        '&:hover fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.4)' : undefined,
                        },
                        '& input': {
                          color: darkMode ? '#fff' : undefined,
                        }
                      }
                    }}
                  />
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    name="password"
                    label="Пароль"
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    autoComplete="new-password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Lock color="primary" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: darkMode ? 'rgba(255,255,255,0.7)' : undefined,
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.23)' : undefined,
                        },
                        '&:hover fieldset': {
                          borderColor: darkMode ? 'rgba(255,255,255,0.4)' : undefined,
                        },
                        '& input': {
                          color: darkMode ? '#fff' : undefined,
                        }
                      }
                    }}
                  />
                </>
              ) : (
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="code"
                  label="Код подтверждения"
                  name="code"
                  autoComplete="off"
                  autoFocus
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  inputProps={{ 
                    maxLength: 4,
                    style: { fontSize: '24px', letterSpacing: '0.5em', textAlign: 'center' }
                  }}
                  sx={{
                    '& .MuiInputLabel-root': {
                      color: darkMode ? 'rgba(255,255,255,0.7)' : undefined,
                    },
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': {
                        borderColor: darkMode ? 'rgba(255,255,255,0.23)' : undefined,
                      },
                      '&:hover fieldset': {
                        borderColor: darkMode ? 'rgba(255,255,255,0.4)' : undefined,
                      },
                      '& input': {
                        color: darkMode ? '#fff' : undefined,
                      }
                    }
                  }}
                />
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  mt: 3,
                  mb: 2,
                  py: 1.5,
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #2196F3 50%, #21CBF3 100%)',
                  },
                }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  step === 1 ? 'Зарегистрироваться' : 'Подтвердить'
                )}
              </Button>

              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Link 
                  component="button"
                  variant="body2"
                  onClick={() => router.push('/auth/login')}
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      textDecoration: 'underline'
                    }
                  }}
                >
                  Уже есть аккаунт? Войти
                </Link>
              </Box>
            </Box>
          </Paper>
        </Box>
      </Container>
    </Box>
  );
}
