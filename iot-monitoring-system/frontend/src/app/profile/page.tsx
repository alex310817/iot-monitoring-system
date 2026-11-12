'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Avatar,
  Alert,
  IconButton,
  CircularProgress,
  ImageList,
  ImageListItem,
  Dialog,
  DialogTitle,
  DialogContent
} from '@mui/material';
import { PhotoCamera, ArrowBack, Wallpaper } from '@mui/icons-material';
import { useRouter } from 'next/navigation';
import { useThemeMode } from '../providers';
import AchievementList from '@/components/AchievementList';
import { useAchievements } from '@/contexts/AchievementContext';

interface Profile {
  display_name: string;
  avatar_url?: string;
  bio?: string;
  email: string;
  background_url?: string;
}

interface PresetBackground {
  id: string;
  url: string;
  name: string;
}

export default function Profile() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    bio: '',
    avatar_url: '',
    background_url: ''
  });
  const [openBackgrounds, setOpenBackgrounds] = useState(false);
  const [presetBackgrounds, setPresetBackgrounds] = useState<PresetBackground[]>([]);
  const [achievements, setAchievements] = useState([]);
  const [newAchievement, setNewAchievement] = useState<{ name: string; icon: string } | null>(null);
  const [achievementType, setAchievementType] = useState<'unlocked' | 'locked'>('unlocked');
  const router = useRouter();
  const { darkMode } = useThemeMode();
  const { showAchievement } = useAchievements();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/auth/login');
      return;
    }
    fetchProfile();
    fetchAchievements();
  }, [router]);

  const fetchProfile = async () => {
    try {
      const response = await fetch('http://localhost:8000/users/me', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setFormData({
          display_name: data.display_name || '',
          bio: data.bio || '',
          avatar_url: data.avatar_url || '',
          background_url: data.background_url || ''
        });
      } else {
        router.push('/auth/login');
      }
    } catch (err) {
      setError('Ошибка при загрузке профиля');
    }
  };

  const fetchPresetBackgrounds = async () => {
    try {
      const response = await fetch('http://localhost:8000/users/backgrounds/presets', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setPresetBackgrounds(Object.entries(data.presets).map(([id, url]) => ({
          id,
          url: `http://localhost:8000${url}`,
          name: id.charAt(0).toUpperCase() + id.slice(1)
        })));
      }
    } catch (err) {
      setError('Ошибка при загрузке фонов');
    }
  };

  const fetchAchievements = async () => {
    try {
      const response = await fetch(`http://localhost:8000/achievements/${achievementType}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAchievements(data);
      }
    } catch (err) {
      setError('Ошибка при загрузке достижений');
    }
  };

  useEffect(() => {
    fetchAchievements();
  }, [achievementType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      if (response.ok) {
        await fetchProfile();
        setIsEditing(false);
        
        // Show achievement popup if unlocked
        if (data.unlocked_achievements?.length > 0) {
          showAchievement(data.unlocked_achievements[0]);
          fetchAchievements(); // Refresh achievements list
        }
      } else {
        throw new Error('Ошибка при обновлении профиля');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files?.length) return;

    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/users/avatar', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(prev => prev ? { ...prev, avatar_url: data.avatar_url } : null);
      } else {
        throw new Error('Ошибка при загрузке аватара');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при загрузке аватара');
    }
  };

  const handleBackgroundUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files?.length) return;

    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/users/background', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(prev => prev ? { ...prev, background_url: data.background_url } : null);
      }
    } catch (err) {
      setError('Ошибка при загрузке фона');
    }
  };

  const handlePresetSelect = async (presetId: string) => {
    try {
      const response = await fetch('http://localhost:8000/users/background/preset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ preset_name: presetId })
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(prev => prev ? { ...prev, background_url: data.background_url } : null);
        setOpenBackgrounds(false);
      }
    } catch (err) {
      setError('Ошибка при установке фона');
    }
  };

  const handleEdit = () => {
    setFormData({
      display_name: profile?.display_name || '',
      bio: profile?.bio || '',
      avatar_url: profile?.avatar_url || '',
      background_url: profile?.background_url || ''
    });
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setFormData({
      display_name: profile?.display_name || '',
      bio: profile?.bio || '',
      avatar_url: profile?.avatar_url || '',
      background_url: profile?.background_url || ''
    });
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
        maxWidth="md" 
        sx={{ 
          py: 4,
          position: 'relative',
          zIndex: 1
        }}
      >
        <Paper 
          elevation={3} 
          sx={{ 
            p: 4, 
            borderRadius: 2, 
            position: 'relative',
            backdropFilter: 'blur(10px)',
            backgroundColor: darkMode ? 'rgba(0, 0, 0, 0.7)' : 'rgba(255, 255, 255, 0.8)',
            backgroundImage: profile?.background_url ? 
              `url(http://localhost:8000${profile.background_url})` : 
              'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: profile?.background_url ? 'rgba(0, 0, 0, 0.5)' : 'transparent',
              borderRadius: 2,
            }
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, gap: 2, position: 'relative', zIndex: 1 }}>
            <IconButton 
              onClick={() => router.push('/dashboard')}
              sx={{ color: profile?.background_url ? 'white' : 'inherit' }}
            >
              <ArrowBack />
            </IconButton>
            <Typography 
              variant="h4"
              sx={{ color: profile?.background_url ? 'white' : 'inherit' }}
            >
              {isEditing ? 'Редактирование профиля' : 'Профиль пользователя'}
            </Typography>
            {!isEditing && (
              <Button
                variant="contained"
                onClick={handleEdit}
                sx={{
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  ml: 'auto'
                }}
              >
                Редактировать
              </Button>
            )}
          </Box>

          {!isEditing ? (
            <>
              <Box sx={{ position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
                  <Avatar
                    sx={{ 
                      width: 100, 
                      height: 100, 
                      mr: 3,
                      border: '3px solid',
                      borderColor: 'primary.main'
                    }}
                    src={profile?.avatar_url ? `http://localhost:8000${profile.avatar_url}` : undefined}
                  >
                    {!profile?.avatar_url && profile?.display_name?.charAt(0)}
                  </Avatar>
                </Box>

                {error && (
                  <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                  </Alert>
                )}

                <Typography 
                  variant="h6" 
                  sx={{ 
                    color: profile?.background_url ? '#fff' : 'inherit',
                    textShadow: profile?.background_url ? '1px 1px 2px rgba(0,0,0,0.5)' : 'none'
                  }}
                >
                  {profile?.display_name}
                </Typography>
                
                <Typography 
                  color={profile?.background_url ? 'rgba(255,255,255,0.8)' : 'textSecondary'} 
                  sx={{ mb: 2 }}
                >
                  {profile?.email}
                </Typography>
                <Typography 
                  paragraph
                  sx={{ 
                    color: profile?.background_url ? '#fff' : 'inherit',
                    textShadow: profile?.background_url ? '1px 1px 2px rgba(0,0,0,0.5)' : 'none'
                  }}
                >
                  {profile?.bio}
                </Typography>
              </Box>
            </>
          ) : (
            <>
              <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ mb: 3 }}>Редактирование профиля</Typography>
                
                <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                  <Button
                    variant="contained"
                    component="label"
                    startIcon={<PhotoCamera />}
                  >
                    Изменить фото
                    <input
                      hidden
                      accept="image/*"
                      type="file"
                      onChange={handleAvatarUpload}
                    />
                  </Button>

                  <Button
                    variant="contained"
                    component="label"
                    startIcon={<Wallpaper />}
                  >
                    Изменить фон
                    <input
                      hidden
                      accept="image/*"
                      type="file"
                      onChange={handleBackgroundUpload}
                    />
                  </Button>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={handleCancel}
                  >
                    Отменить
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleSubmit}
                    sx={{
                      background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                    }}
                  >
                    Сохранить
                  </Button>
                </Box>

                <Box component="form" sx={{ mt: 3 }}>
                  <TextField
                    fullWidth
                    label="Имя"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    margin="normal"
                    required
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: profile?.background_url ? '#fff' : undefined,
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: profile?.background_url ? 'rgba(255,255,255,0.5)' : undefined,
                        },
                        '&:hover fieldset': {
                          borderColor: profile?.background_url ? '#fff' : undefined,
                        },
                        '& input': {
                          color: profile?.background_url ? '#fff' : undefined,
                        }
                      }
                    }}
                  />
                  <TextField
                    fullWidth
                    label="О себе"
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    margin="normal"
                    multiline
                    rows={4}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: profile?.background_url ? '#fff' : undefined,
                      },
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: profile?.background_url ? 'rgba(255,255,255,0.5)' : undefined,
                        },
                        '&:hover fieldset': {
                          borderColor: profile?.background_url ? '#fff' : undefined,
                        },
                        '& input': {
                          color: profile?.background_url ? '#fff' : undefined,
                        }
                      }
                    }}
                  />
                </Box>
              </Box>
            </>
          )}
          <Box sx={{ mt: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Достижения</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant={achievementType === 'unlocked' ? 'contained' : 'outlined'}
                  onClick={() => setAchievementType('unlocked')}
                  sx={{
                    bgcolor: achievementType === 'unlocked' ? 'success.main' : undefined,
                  }}
                >
                  Разблокированные
                </Button>
                <Button
                  variant={achievementType === 'locked' ? 'contained' : 'outlined'}
                  onClick={() => setAchievementType('locked')}
                  sx={{
                    bgcolor: achievementType === 'locked' ? 'grey.700' : undefined,
                  }}
                >
                  Заблокированные
                </Button>
              </Box>
            </Box>
            <AchievementList achievements={achievements} />
          </Box>
        </Paper>

        <Dialog open={openBackgrounds} onClose={() => setOpenBackgrounds(false)} maxWidth="md">
          <DialogTitle>Выберите фон</DialogTitle>
          <DialogContent>
            <ImageList sx={{ width: 500, height: 450 }} cols={3} rowHeight={164}>
              {presetBackgrounds.map((background) => (
                <ImageListItem 
                  key={background.id}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': { opacity: 0.8 }
                  }}
                  onClick={() => handlePresetSelect(background.id)}
                >
                  <img
                    src={background.url}
                    alt={background.name}
                    loading="lazy"
                    style={{ height: '100%', objectFit: 'cover' }}
                  />
                </ImageListItem>
              ))}
            </ImageList>
          </DialogContent>
        </Dialog>
      </Container>
    </Box>
  );
}
