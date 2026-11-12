'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, PowerSettingsNew, AccountCircle, Logout, Search as SearchIcon, Brightness4, Brightness7 } from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useThemeMode } from '../providers';
import { useAchievements } from '@/contexts/AchievementContext';
import { memo } from 'react';
import debounce from 'lodash.debounce';

interface Device {
  id: number;
  name: string;
  description?: string;
  status: boolean;
}

interface USBDevice {
  id: string;
  name: string;
  manufacturer: string;
  status: boolean;
}

// Мемоизация компонентов для предотвращения лишних ререндеров
interface DeviceCardProps {
  device: Device;
  onToggle: (id: number, status: boolean) => void;
  onDelete: (id: number) => void;
}

const DeviceCard = memo(({ device, onToggle, onDelete }: DeviceCardProps) => {
  return (
    <Grid item xs={12} sm={6} md={4} key={device.id}>
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" component="h2">
              {device.name}
            </Typography>
            <Box>
              <IconButton
                onClick={() => onToggle(device.id, device.status)}
                color={device.status ? "primary" : "default"}
              >
                <PowerSettingsNew />
              </IconButton>
              <IconButton
                onClick={() => onDelete(device.id)}
                color="error"
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          </Box>
          <Typography color="textSecondary">
            {device.description}
          </Typography>
          <Typography color={device.status ? "primary" : "error"}>
            Статус: {device.status ? 'Включено' : 'Выключено'}
          </Typography>
        </CardContent>
      </Card>
    </Grid>
  );
});

export default function Dashboard() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newDevice, setNewDevice] = useState({ name: '', description: '' });
  const [error, setError] = useState('');
  const [scanning, setScanning] = useState(false);
  const router = useRouter();
  const { darkMode, toggleTheme } = useThemeMode();
  const { showAchievement } = useAchievements();

  // Добавляем дебаунс для поиска устройств
  const debouncedFetchDevices = useCallback(
    debounce(() => {
      fetchDevices();
    }, 300),
    []
  );

  // Оптимизируем загрузку данных
  useEffect(() => {
    const controller = new AbortController();
    
    const loadData = async () => {
      try {
        await Promise.all([
          fetchDevices(controller.signal),
          // другие параллельные запросы
        ]);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return;
        setError('Ошибка при загрузке данных');
      }
    };

    loadData();
    return () => controller.abort();
  }, [router]);

  const refreshToken = async () => {
    try {
      const response = await fetch('http://localhost:8000/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const fetchWithRefresh = async (url: string, options: RequestInit) => {
    let response = await fetch(url, options);
    
    if (response.status === 401) {
      const refreshed = await refreshToken();
      if (refreshed) {
        // Retry with new token
        options.headers = {
          ...options.headers,
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        };
        response = await fetch(url, options);
      } else {
        router.push('/auth/login');
      }
    }
    return response;
  };

  const fetchDevices = async (signal?: AbortSignal) => {
    try {
      const response = await fetchWithRefresh('http://localhost:8000/devices/', {  // Добавлен слеш в конце URL
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        signal
      });
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (err) {
      setError('Ошибка при загрузке устройств');
    }
  };

  const handleAddDevice = async () => {
    try {
      const response = await fetch('http://localhost:8000/devices/', {  // Add trailing slash
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: newDevice.name,
          description: newDevice.description,
          status: false
        })
      });

      const data = await response.json();
      if (response.ok) {
        setOpenDialog(false);
        setNewDevice({ name: '', description: '' });
        fetchDevices();
        
        // Show achievement if unlocked
        if (data.unlocked_achievements && data.unlocked_achievements.length > 0) {
          // Show only the first achievement if multiple are unlocked
          const achievement = data.unlocked_achievements[0];
          showAchievement({
            name: achievement.name,
            icon: achievement.icon || 'EmojiEvents' // Используем дефолтную иконку если нет своей
          });
        }
      }
    } catch (err) {
      setError('Ошибка при добавлении устройства');
    }
  };

  const toggleDevice = async (deviceId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`http://localhost:8000/devices/${deviceId}/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          action: currentStatus ? 'off' : 'on'
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Обновляем список устройств после успешного переключения
        await fetchDevices();
        
        // Проверяем наличие достижений
        if (data.unlocked_achievements?.length > 0) {
          data.unlocked_achievements.forEach((achievement: any) => {
            showAchievement({
              name: achievement.name,
              icon: achievement.icon
            });
          });
        }
      } else {
        throw new Error('Failed to toggle device');
      }
    } catch (err) {
      setError('Ошибка при управлении устройством');
    }
  };

  const handleDeleteDevice = async (deviceId: number) => {
    try {
      await fetch(`http://localhost:8000/devices/${deviceId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      fetchDevices();
    } catch (err) {
      setError('Ошибка при удалении устройства');
    }
  };

  const handleScanDevices = async () => {
    setScanning(true);
    try {
      const response = await fetch('http://localhost:8000/devices/scan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Обновляем список устройств с новыми данными
        await fetchDevices();
      }
    } catch (err) {
      setError('Ошибка при поиске устройств');
    } finally {
      setScanning(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/auth/login');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
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
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 0,
        }
      }}
    >
      <Container 
        maxWidth="lg" 
        sx={{ 
          py: 4,
          position: 'relative',
          zIndex: 1
        }}
      >
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4" component="h1">
            Умные устройства
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <IconButton onClick={toggleTheme} color="inherit">
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleScanDevices}
              disabled={scanning}
              sx={{
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              }}
            >
              {scanning ? 'Поиск...' : 'Найти устройства'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<AccountCircle />}
              onClick={() => router.push('/profile')}
            >
              Профиль
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpenDialog(true)}
              sx={{
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              }}
            >
              Добавить устройство
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<Logout />}
              onClick={handleLogout}
            >
              Выйти
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {devices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onToggle={toggleDevice}
              onDelete={handleDeleteDevice}
            />
          ))}
        </Grid>

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
          <DialogTitle>Добавить новое устройство</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Название устройства"
              fullWidth
              value={newDevice.name}
              onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
            />
            <TextField
              margin="dense"
              label="Описание"
              fullWidth
              multiline
              rows={3}
              value={newDevice.description}
              onChange={(e) => setNewDevice({ ...newDevice, description: e.target.value })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Отмена</Button>
            <Button onClick={handleAddDevice} variant="contained">Добавить</Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
}
