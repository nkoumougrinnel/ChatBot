/**
 * PWA - Gestion de l'installation et des mises à jour
 * SUP'ONE AI - Version stabilisée SANS rafraîchissements intempestifs
 */

// Variables globales
let deferredPrompt;
let swRegistration = null;
let offlineTimeout = null;
let isTransitioningToOffline = false;

// Détection du mode PWA
const isPWA = () => {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true ||
    document.referrer.includes('android-app://')
  );
};

// Enregistrer le Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      swRegistration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/',
      });
      
      console.log('[PWA] Service Worker enregistré:', swRegistration.scope);

      // Vérifier les mises à jour
      swRegistration.addEventListener('updatefound', () => {
        const newWorker = swRegistration.installing;
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // ✅ SEULEMENT si une mise à jour est détectée
            showUpdateBanner();
          }
        });
      });

      // Vérifier les mises à jour toutes les heures
      setInterval(() => {
        swRegistration.update();
      }, 60 * 60 * 1000);

    } catch (error) {
      console.error('[PWA] Erreur Service Worker:', error);
    }
  });
}

// Écouter l'événement beforeinstallprompt
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('[PWA] Prompt d\'installation disponible');
  
  e.preventDefault();
  deferredPrompt = e;
  
  // ✅ SEULEMENT afficher si beforeinstallprompt est déclenché ET pas en mode PWA
  if (!isPWA()) {
    setTimeout(() => {
      showInstallBanner();
    }, 1500);
  }
});

// Afficher la bannière d'installation
function showInstallBanner() {
  const banner = document.getElementById('install-banner');
  if (!banner) {
    console.warn('[PWA] Bannière d\'installation introuvable dans le DOM');
    return;
  }

  // Toujours afficher tant que pas installé
  if (isPWA()) {
    console.log('[PWA] Application déjà installée');
    return;
  }

  // ✅ Utiliser display: block au lieu de flex (correspond au CSS)
  banner.style.display = 'block';
  banner.offsetHeight;
  
  requestAnimationFrame(() => {
    banner.classList.add('show');
  });

  console.log('[PWA] Bannière d\'installation affichée');

  // Bouton Installer
  const installBtn = document.getElementById('install-btn');
  if (installBtn) {
    const newInstallBtn = installBtn.cloneNode(true);
    installBtn.parentNode.replaceChild(newInstallBtn, installBtn);
    newInstallBtn.addEventListener('click', installApp);
  }

  // Bouton Fermer (X)
  const closeBtn = document.getElementById('close-install-btn');
  if (closeBtn) {
    const newCloseBtn = closeBtn.cloneNode(true);
    closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
    newCloseBtn.addEventListener('click', hideInstallBanner);
  }
}

// Cacher la bannière d'installation temporairement
function hideInstallBanner() {
  const banner = document.getElementById('install-banner');
  if (!banner) return;
  
  banner.classList.remove('show');
  
  setTimeout(() => {
    banner.style.display = 'none';
  }, 300);
  
  console.log('[PWA] Bannière d\'installation masquée temporairement');
}

// Installer l'application
async function installApp() {
  if (!deferredPrompt) {
    console.log('[PWA] Pas de prompt d\'installation disponible');
    showToast('Installation non disponible pour le moment', 'warning');
    return;
  }

  console.log('[PWA] Lancement de l\'installation...');

  deferredPrompt.prompt();

  const { outcome } = await deferredPrompt.userChoice;
  console.log('[PWA] Choix utilisateur:', outcome);

  if (outcome === 'accepted') {
    console.log('[PWA] Application installée avec succès');
    hideInstallBanner();
    showToast('Application installée avec succès !', 'success');
    
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_install', {
        event_category: 'engagement',
        event_label: 'PWA Installation',
      });
    }
  } else {
    console.log('[PWA] Installation refusée');
    hideInstallBanner();
  }

  deferredPrompt = null;
}

// Détecter quand l'app est installée
window.addEventListener('appinstalled', () => {
  console.log('[PWA] Application installée');
  hideInstallBanner();
  showToast('Application installée ! Vous pouvez la lancer depuis votre écran d\'accueil', 'success');
  
  if (typeof gtag !== 'undefined') {
    gtag('event', 'pwa_installed', {
      event_category: 'engagement',
      event_label: 'PWA Installed',
    });
  }
});

// Afficher la bannière de mise à jour
function showUpdateBanner() {
  const banner = document.getElementById('update-banner');
  if (!banner) {
    console.warn('[PWA] Bannière de mise à jour introuvable');
    return;
  }

  banner.style.display = 'flex';
  banner.offsetHeight;
  
  requestAnimationFrame(() => {
    banner.classList.add('show');
  });

  console.log('[PWA] Mise à jour disponible');

  const updateBtn = document.getElementById('update-btn');
  if (updateBtn) {
    const newUpdateBtn = updateBtn.cloneNode(true);
    updateBtn.parentNode.replaceChild(newUpdateBtn, updateBtn);
    
    newUpdateBtn.addEventListener('click', () => {
      console.log('[PWA] Application de la mise à jour...');
      
      if (swRegistration && swRegistration.waiting) {
        swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
      
      window.location.reload();
    });
  }
}

// ✅ CORRECTION : Détection plus intelligente de la connexion
window.addEventListener('online', () => {
  console.log('[PWA] Connexion rétablie');
  
  // Annuler toute redirection en cours
  if (offlineTimeout) {
    clearTimeout(offlineTimeout);
    offlineTimeout = null;
  }
  
  isTransitioningToOffline = false;
  updateConnectionStatus(true);
  showToast('Connexion rétablie', 'success');
  
  // ✅ Revenir à la page principale UNIQUEMENT depuis offline.html
  // ❌ NE PAS rediriger depuis demo.html (l'utilisateur veut rester sur la démo)
  if (window.location.pathname.includes('offline.html')) {
    console.log('[PWA] Retour à la page principale depuis offline.html');
    window.location.href = '/';
  } else if (window.location.pathname.includes('demo.html')) {
    console.log('[PWA] Connexion rétablie - L\'utilisateur reste sur demo.html');
  } else {
    console.log('[PWA] Connexion rétablie sur la page actuelle');
  }
});

window.addEventListener('offline', () => {
  console.log('[PWA] Événement offline détecté');
  
  // Annuler tout timeout précédent
  if (offlineTimeout) {
    clearTimeout(offlineTimeout);
  }
  
  updateConnectionStatus(false);
  showToast('Mode hors ligne activé', 'warning');
  
  // ✅ Redirection intelligente : uniquement si on n'est pas déjà sur une page offline
  if (!window.location.pathname.includes('offline.html') && 
      !window.location.pathname.includes('demo.html')) {
    
    console.log('[PWA] Redirection vers offline.html dans 3 secondes...');
    
    // Attendre 3 secondes pour éviter les faux positifs
    offlineTimeout = setTimeout(() => {
      // Vérifier à nouveau qu'on est toujours offline
      if (!navigator.onLine) {
        console.log('[PWA] Toujours offline, redirection...');
        window.location.href = '/offline.html';
      }
    }, 3000);
  } else {
    console.log('[PWA] Déjà sur une page offline, pas de redirection');
  }
});

// ✅ Fonction pour vérifier réellement la connexion (pas juste navigator.onLine)
async function checkRealConnection() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const response = await fetch('/manifest.json', {
      method: 'HEAD',
      cache: 'no-cache',
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch (error) {
    return false;
  }
}

// Mettre à jour le statut de connexion
function updateConnectionStatus(isOnline) {
  const statusElement = document.getElementById('connection-status');
  const statusDot = document.querySelector('.status-dot');
  const statusIndicator = document.querySelector('.status-indicator');
  
  if (statusElement) {
    statusElement.textContent = isOnline ? 'En ligne' : 'Hors ligne';
  }
  
  if (statusDot) {
    if (isOnline) {
      statusDot.style.background = 'var(--success, #10b981)';
      statusDot.classList.remove('offline');
    } else {
      statusDot.style.background = '#f59e0b';
      statusDot.classList.add('offline');
    }
  }
  
  if (statusIndicator) {
    if (isOnline) {
      statusIndicator.classList.remove('offline');
    } else {
      statusIndicator.classList.add('offline');
    }
  }
}

// Fonction helper pour afficher des toasts
function showToast(message, type = 'info', duration = 3000) {
  const toast = document.getElementById('toast');
  if (!toast) {
    console.warn('[PWA] Élément toast introuvable');
    return;
  }

  // Icônes Bootstrap Icons selon le type
  let icon = '';
  switch(type) {
    case 'success':
      icon = '<i class="bi bi-check-circle-fill"></i>';
      toast.className = 'toast toast-success';
      break;
    case 'warning':
      icon = '<i class="bi bi-exclamation-triangle-fill"></i>';
      toast.className = 'toast toast-warning';
      break;
    case 'error':
      icon = '<i class="bi bi-x-circle-fill"></i>';
      toast.className = 'toast toast-error';
      break;
    default:
      icon = '<i class="bi bi-info-circle-fill"></i>';
      toast.className = 'toast toast-info';
  }

  toast.innerHTML = `${icon} <span>${message}</span>`;
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, duration);
}

// ✅ Initialisation au chargement - Avec vérification offline intelligente
window.addEventListener('load', async () => {
  console.log('[PWA] Script initialisé');
  
  // Vérifier le statut de connexion initial
  const isOnline = navigator.onLine;
  updateConnectionStatus(isOnline);
  
  // ✅ Vérification offline au chargement
  // Rediriger SEULEMENT si :
  // 1. On est hors ligne
  // 2. On n'est pas déjà sur offline.html ou demo.html
  // 3. La page n'a pas déjà été mise en cache
  if (!isOnline && 
      !window.location.pathname.includes('offline.html') && 
      !window.location.pathname.includes('demo.html')) {
    
    console.log('[PWA] Page chargée en mode offline, vérification...');
    
    // Attendre 2 secondes pour laisser le Service Worker gérer la requête
    setTimeout(async () => {
      // Double vérification de la connexion
      const stillOffline = !navigator.onLine;
      const reallyOffline = !(await checkRealConnection());
      
      if (stillOffline || reallyOffline) {
        console.log('[PWA] Toujours offline, redirection vers offline.html');
        window.location.href = '/offline.html';
      }
    }, 2000);
  }
  
  if (isPWA()) {
    console.log('[PWA] Application lancée en mode standalone');
    
    // Masquer la bannière d'installation en mode PWA
    const banner = document.getElementById('install-banner');
    if (banner) {
      banner.style.display = 'none';
    }
    
    if (typeof gtag !== 'undefined') {
      gtag('event', 'pwa_launch', {
        event_category: 'engagement',
        event_label: 'PWA Launch',
      });
    }
  } else {
    console.log('[PWA] Application lancée en mode navigateur');
    console.log('[PWA] En attente de l\'événement beforeinstallprompt...');
  }
});

// Gestion du partage
if (navigator.share) {
  window.shareContent = async (title, text, url) => {
    try {
      await navigator.share({
        title: title || 'SUP\'ONE AI',
        text: text || 'Découvrez SUP\'ONE AI, l\'assistant intelligent',
        url: url || window.location.href,
      });
      console.log('[PWA] Contenu partagé');
      showToast('Partagé avec succès !', 'success');
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('[PWA] Erreur de partage:', error);
      }
    }
  };
}

// Détection du mode standalone
if (window.matchMedia('(display-mode: standalone)').matches) {
  document.addEventListener('gesturestart', (e) => {
    e.preventDefault();
  });
  
  console.log('[PWA] Mode standalone détecté');
}

// Prévenir le pull-to-refresh sur mobile
let startY = 0;
document.addEventListener('touchstart', (e) => {
  startY = e.touches[0].pageY;
}, { passive: true });

document.addEventListener('touchmove', (e) => {
  const y = e.touches[0].pageY;
  const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
  
  if (scrollTop === 0 && y > startY) {
    e.preventDefault();
  }
}, { passive: false });

// Fonction debug pour forcer l'affichage (TEST UNIQUEMENT)
window.showPWAInstallBanner = () => {
  console.log('[DEBUG] Affichage forcé de la bannière d\'installation');
  showInstallBanner();
};

// Fonction debug pour forcer la bannière de mise à jour (TEST UNIQUEMENT)
window.showPWAUpdateBanner = () => {
  console.log('[DEBUG] Affichage forcé de la bannière de mise à jour');
  showUpdateBanner();
};

// ✅ Fonction debug pour tester le statut de connexion
window.testConnection = async () => {
  const real = await checkRealConnection();
  const reported = navigator.onLine;
  console.log('[DEBUG] Test de connexion:');
  console.log('  - navigator.onLine:', reported);
  console.log('  - Connexion réelle:', real);
  return { reported, real };
};

console.log('[PWA] Script chargé - Version stabilisée');
console.log('[DEBUG] Commandes disponibles:');
console.log('  - window.showPWAInstallBanner() : Forcer la bannière d\'installation');
console.log('  - window.showPWAUpdateBanner() : Forcer la bannière de mise à jour');
console.log('  - window.testConnection() : Tester la connexion réelle');