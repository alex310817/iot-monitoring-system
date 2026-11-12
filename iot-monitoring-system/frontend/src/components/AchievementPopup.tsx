import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paper, Typography, Box } from '@mui/material';
import * as Icons from '@mui/icons-material';
import { EmojiEvents } from '@mui/icons-material';

interface AchievementPopupProps {
  achievement: {
    name: string;
    icon: string;
  } | null;
}

export default function AchievementPopup({ achievement }: AchievementPopupProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Create new Audio element with the correct path
    const audio = new Audio('/sounds/achievement-unlocked.mp3');
    audio.preload = 'auto';  // Ensure audio is preloaded
    audio.volume = 0.5;
    
    // Store the audio element in the ref
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (achievement && audioRef.current) {
      try {
        audioRef.current.currentTime = 0;  // Reset playback position
        audioRef.current.play().catch(error => {
          console.warn('Audio playback failed:', error);
        });
      } catch (error) {
        console.error('Error playing achievement sound:', error);
      }
    }
  }, [achievement]);

  return (
    <AnimatePresence>
      {achievement && (
        <motion.div
          initial={{ y: 50, x: '-50%', opacity: 0, scale: 0.5 }}
          animate={{ 
            y: 0, 
            opacity: 1, 
            scale: 1,
            transition: {
              type: "spring",
              stiffness: 300,
              damping: 25
            }
          }}
          exit={{ 
            y: -50, 
            opacity: 0,
            scale: 0.5,
            transition: { duration: 0.2 }
          }}
          style={{
            position: 'fixed',
            bottom: 40,
            left: '50%',
            zIndex: 2000,
            transformOrigin: 'center'
          }}
        >
          <Paper
            elevation={6}
            sx={{
              p: 3,
              background: 'linear-gradient(45deg, #FF9800 30%, #FFD700 90%)',
              color: 'white',
              minWidth: 350,
              borderRadius: 3,
              boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
            }}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center',
                gap: 2,
                position: 'relative',
              }}>
                {/* Achievement Icon */}
                <Box sx={{ 
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  borderRadius: '50%',
                  p: 1,
                }}>
                  {/* @ts-ignore */}
                  {Icons[achievement.icon] && React.createElement(Icons[achievement.icon], {
                    sx: { fontSize: 40 }
                  })}
                </Box>

                {/* Text Content */}
                <Box>
                  <Typography 
                    variant="overline" 
                    sx={{ 
                      opacity: 0.9,
                      fontWeight: 'bold',
                      letterSpacing: 2,
                      textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
                    }}
                  >
                    ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО!
                  </Typography>
                  <Typography 
                    variant="h6"
                    sx={{
                      fontWeight: 'bold',
                      textShadow: '1px 1px 2px rgba(0,0,0,0.3)'
                    }}
                  >
                    {achievement.name}
                  </Typography>
                </Box>

                {/* Trophy Icon */}
                <motion.div
                  animate={{ 
                    rotate: [0, -15, 15, -15, 15, 0],
                    scale: [1, 1.3, 1],
                    y: [0, -10, 0]
                  }}
                  transition={{ 
                    duration: 1.5,
                    delay: 0.3,
                    repeat: 1
                  }}
                >
                  <EmojiEvents 
                    sx={{ 
                      position: 'absolute',
                      top: -25,
                      right: -25,
                      fontSize: 50,
                      color: '#FFD700',
                      filter: 'drop-shadow(3px 3px 5px rgba(0,0,0,0.3))'
                    }} 
                  />
                </motion.div>
              </Box>
            </motion.div>
          </Paper>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
