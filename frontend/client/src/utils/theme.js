// Theme utility functions
export function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'dark';
  const root = document.documentElement;
  
  if (savedTheme === 'light') {
    root.classList.add('light-mode');
  } else {
    root.classList.remove('light-mode');
  }
  
  return savedTheme;
}

export function toggleTheme() {
  const root = document.documentElement;
  const isLight = root.classList.toggle('light-mode');
  
  if (isLight) {
    localStorage.setItem('theme', 'light');
    return 'light';
  } else {
    localStorage.setItem('theme', 'dark');
    return 'dark';
  }
}

export function getTheme() {
  const root = document.documentElement;
  return root.classList.contains('light-mode') ? 'light' : 'dark';
}

