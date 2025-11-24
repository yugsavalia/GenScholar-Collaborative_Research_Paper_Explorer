import { useState, useEffect } from 'react';
import { initTheme, toggleTheme, getTheme } from '../utils/theme';

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return getTheme();
    }
    return 'dark';
  });

  useEffect(() => {
    initTheme();
    setTheme(getTheme());
  }, []);

  const toggle = () => {
    const newTheme = toggleTheme();
    setTheme(newTheme);
  };

  return { theme, toggle };
}

