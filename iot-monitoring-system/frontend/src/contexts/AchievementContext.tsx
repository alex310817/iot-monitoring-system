import React, { createContext, useContext, useState, useCallback } from 'react';
import AchievementPopup from '@/components/AchievementPopup';  // Fixed import

interface Achievement {
  name: string;
  icon: string;
}

interface AchievementContextType {
  showAchievement: (achievement: Achievement) => void;
  currentAchievement: Achievement | null;
}

const AchievementContext = createContext<AchievementContextType>({
  showAchievement: () => {},
  currentAchievement: null,
});

// Export hook for use in components
export const useAchievements = () => {
  const context = useContext(AchievementContext);
  if (!context) {
    throw new Error('useAchievements must be used within an AchievementProvider');
  }
  return context;
};

export function AchievementProvider({ children }: { children: React.ReactNode }) {
  const [currentAchievement, setCurrentAchievement] = useState<Achievement | null>(null);
  const [showingAchievement, setShowingAchievement] = useState(false);

  const showAchievement = useCallback((achievement: Achievement) => {
    if (!achievement || showingAchievement) return;
    
    setShowingAchievement(true);
    setCurrentAchievement(achievement);

    // Hide achievement after 5 seconds
    setTimeout(() => {
      setCurrentAchievement(null);
      setShowingAchievement(false);
    }, 5000);
  }, [showingAchievement]);

  return (
    <AchievementContext.Provider value={{ showAchievement, currentAchievement }}>
      {children}
      <AchievementPopup achievement={currentAchievement} />
    </AchievementContext.Provider>
  );
}
