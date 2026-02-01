// ==========================================
// Studio SWE - Moonlight Edition
// ==========================================

// Smooth scroll till generatorn
function scrollToCreate() {
    const element = document.getElementById('create');
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // Fokusera input efter scroll
        setTimeout(() => {
            const input = document.getElementById('youtubeUrl');
            if (input) input.focus();
        }, 500);
    }
}

// Visa demo (placeholder för framtida video-modal)
function showDemo() {
    // Subtil toast istället för alert
    showToast('Demo-video laddas snart...');
}

// Huvudfunktion: Generera klipp
function generate() {
    const input = document.getElementById('youtubeUrl');
    const results = document.getElementById('results');
    const btn = document.querySelector('.generate-btn');
    const url = input.value.trim();
    
    // Validering
    if (!url || !isValidUrl(url)) {
        input.style.borderColor = '#ef4444';
        input.style.transition = 'border-color 0.3s';
        
        setTimeout(() => {
            input.style.borderColor = '';
        }, 2000);
        
        showToast('Vänligen ange en giltig länk');
        return;
    }
    
    // Loading state
    const originalText = btn.textContent;
    btn.textContent = 'Analyserar video...';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    // Simulera AI-bearbetning
    setTimeout(() => {
        // Visa resultat
        results.classList.add('active');
        
        // Återställ knapp
        btn.textContent = originalText;
        btn.disabled = false;
        btn.style.opacity = '1';
        
        // Scrolla till resultat
        setTimeout(() => {
            results.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
        
        showToast('3 klipp genererade');
        
        // Spara i localStorage för persistence
        saveToHistory(url);
        
    }, 1500);
}

// Validera YouTube URL
function isValidUrl(url) {
    const patterns = [
        /youtube\.com\/watch\?v=/i,
        /youtu\.be\//i,
        /youtube\.com\/shorts\//i
    ];
    return patterns.some(pattern => pattern.test(url));
}

// Toast-notifikation (subtil, matchar designen)
function showToast(message) {
    // Ta bort gammal toast om finns
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        left: 50%;
        transform: translateX(-50%) translateY(20px);
        background: #141D26;
        color: #8BA5C7;
        padding: 0.8rem 1.5rem;
        border-radius: 6px;
        border: 1px solid rgba(91, 141, 190, 0.2);
        font-size: 0.9rem;
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 9999;
        backdrop-filter: blur(10px);
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });
    
    // Ta bort efter 3 sek
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Spara historik i localStorage
function saveToHistory(url) {
    try {
        let history = JSON.parse(localStorage.getItem('studio_swe_history') || '[]');
        history.unshift({
            url: url,
            date: new Date().toISOString(),
            clips: 3
        });
        // Max 10 items
        history = history.slice(0, 10);
        localStorage.setItem('studio_swe_history', JSON.stringify(history));
    } catch (e) {
        console.log('Could not save history');
    }
}

// Mobile menu toggle
function toggleMenu() {
    // Enkel mobilmeny - kan byggas ut senare
    const menu = document.createElement('div');
    menu.innerHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(11, 16, 22, 0.98);
            z-index: 999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2rem;
        ">
            <a href="#features" style="color: #E8EEF4; text-decoration: none; font-size: 1.5rem;" onclick="this.parentElement.remove()">Om</a>
            <a href="#create" style="color: #E8EEF4; text-decoration: none; font-size: 1.5rem;" onclick="this.parentElement.remove()">Skapa</a>
            <a href="#" style="color: #5B8DBE; text-decoration: none; font-size: 1.5rem;" onclick="this.parentElement.remove()">Kontakt</a>
            <button onclick="this.parentElement.remove()" style="
                position: absolute;
                top: 1.5rem;
                right: 5%;
                background: none;
                border: none;
                color: #E8EEF4;
                font-size: 2rem;
                cursor: pointer;
            ">×</button>
        </div>
    `;
    document.body.appendChild(menu.firstElementChild);
}

// Event listeners när DOM är redo
document.addEventListener('DOMContentLoaded', () => {
    // Enter-tangent i input
    const urlInput = document.getElementById('youtubeUrl');
    if (urlInput) {
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                generate();
            }
        });
        
        // Clear error on input
        urlInput.addEventListener('input', () => {
            urlInput.style.borderColor = '';
        });
    }
    
    // Subtil parallax på scroll
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        if (hero && scrolled < 500) {
            hero.style.transform = `translateY(${scrolled * 0.1}px)`;
            hero.style.opacity = 1 - (scrolled * 0.001);
        }
    });
    
    console.log('Studio SWE loaded');
});
