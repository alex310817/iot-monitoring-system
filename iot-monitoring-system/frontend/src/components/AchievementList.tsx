import React from 'react';
import { Box, Grid, Paper, Typography, LinearProgress, Tooltip, Divider } from '@mui/material';
import * as MuiIcons from '@mui/icons-material';

interface Achievement {
  id: number;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress: number;
  condition_value: number;
  unlocked_at?: string;
}

export default function AchievementList({ achievements }: { achievements: Achievement[] }) {
  const lockedStyle = {
    filter: 'grayscale(1)',
    opacity: 0.7,
  };

  const renderIcon = (iconName: string) => {
    // @ts-ignore
    const Icon = MuiIcons[iconName];
    return Icon ? <Icon sx={{ mr: 1, fontSize: 30 }} /> : null;
  };

  const renderLargeIcon = (iconName: string) => {
    // @ts-ignore
    const Icon = MuiIcons[iconName];
    return Icon ? <Icon sx={{ fontSize: 100 }} /> : null;
  };

  if (!achievements?.length) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          Достижения не найдены
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {achievements.map((achievement) => (
        <Grid item xs={12} sm={6} md={4} key={achievement.id}>
          <Paper
            elevation={achievement.unlocked ? 6 : 1}
            sx={{
              p: 3,
              height: '100%',
              position: 'relative',
              overflow: 'hidden',
              background: achievement.unlocked 
                ? 'linear-gradient(135deg, #2196F3 0%, #21CBF3 100%)'
                : 'default',
              color: achievement.unlocked ? 'white' : 'inherit',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-5px)',
                boxShadow: 8,
              },
              ...(achievement.unlocked ? {} : lockedStyle),
            }}
          >
            {/* Background Icon */}
            <Box 
              sx={{ 
                position: 'absolute',
                right: -20,
                top: -20,
                opacity: 0.1,
                transform: 'rotate(15deg)',
              }}
            >
              {renderLargeIcon(achievement.icon)}
            </Box>

            {/* Content */}
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {renderIcon(achievement.icon)}
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  {achievement.name}
                </Typography>
              </Box>

              <Typography variant="body2" sx={{ mb: 2, opacity: 0.9 }}>
                {achievement.description}
              </Typography>

              <Divider sx={{ my: 2, opacity: 0.2 }} />

              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" sx={{ mb: 1, display: 'block' }}>
                  {achievement.unlocked ? (
                    'Достижение разблокировано!'
                  ) : (
                    `Прогресс: ${achievement.progress} / ${achievement.condition_value}`
                  )}
                </Typography>
                <Tooltip 
                  title={achievement.unlocked ? 
                    'Достижение разблокировано' : 
                    `${Math.round((achievement.progress / achievement.condition_value) * 100)}%`
                  }
                >
                  <LinearProgress
                    variant="determinate"
                    value={achievement.unlocked ? 100 : (achievement.progress / achievement.condition_value) * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: achievement.unlocked ? '#4CAF50' : undefined,
                      }
                    }}
                  />
                </Tooltip>
              </Box>

              {achievement.unlocked && achievement.unlocked_at && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    mt: 2, 
                    display: 'block',
                    color: achievement.unlocked ? 'rgba(255,255,255,0.8)' : 'text.secondary'
                  }}
                >
                  Получено: {new Date(achievement.unlocked_at).toLocaleDateString()}
                </Typography>
              )}

              {!achievement.unlocked && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%) rotate(-15deg)',
                    border: '2px solid',
                    borderColor: 'text.secondary',
                    padding: '4px 12px',
                    borderRadius: 1,
                    opacity: 0.5,
                  }}
                >
                  <Typography variant="body2">ЗАКРЫТО</Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
}
