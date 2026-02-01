// ==========================================
// VIRAL STUDIO PRO - Komplett JavaScript
// ==========================================

console.log('✅ Viral Studio Pro laddad!');

// Globala variabler
let valtFormat = null;
let valtFormatData = null;

// Format-data för de 12 mallarna
const formatData = {
    'chockerande-fakta': {
        namn: 'Chockerande fakta',
        emoji: '😱',
        hook: 'Det här visste du INTE...',
        virality: 95,
        struktur: ['Hook', 'Fakta', 'Bevis', 'CTA']
    },
    'sluta-gora-detta': {
        namn: 'Sluta göra detta',
        emoji: '❌',
        hook: 'Vanliga misstag som dödar...',
        virality: 92,
        struktur: ['Misstag', 'Konsekvens', 'Lösning', 'Resultat']
    },
    'hemligt-knep': {
        namn: 'Hemligt knep',
        emoji: '🤫',
        hook: '99% känner inte till...',
        virality: 89,
        struktur: ['Hemlighet', 'Demonstration', 'Fördelar', 'Hur du får det']
    },
    'storytime': {
        namn: 'Storytime',
        emoji: '📖',
        hook: 'Detta hände igår...',
        virality: 94,
        struktur: ['Setup', 'Konflikt', 'Klimax', 'Lärdom']
    },
    'pov': {
        namn: 'POV',
        emoji: '👁️',
        hook: 'POV: Du är AI-expert...',
        virality: 91,
        struktur: ['Situation', 'Upplevelse', 'Reaktion', 'Twist']
    },
    'day-in-life': {
        namn: 'Day in Life',
        emoji: '☀️',
        hook: 'En dag som AI-utvecklare',
        virality: 88,
        struktur: ['Morgon', 'Arbete', 'Höjdpunkt', 'Avslutning']
    },
    'myt-vs-fakta': {
        namn: 'Myt vs Fakta',
        emoji: '🦄',
        hook: '3 lögner om AI...',
        virality: 90,
        struktur: ['Myt 1', 'Fakta 1', 'Myt 2', 'Fakta 2']
    },
    'reaktion': {
        namn: 'Reaktion',
        emoji: '😲',
        hook: 'Jag chockades av detta...',
        virality: 93,
        struktur: ['Setup', 'Reveal', 'Reaktion', 'Analys']
    },
    'snabb-tutorial': {
        namn: 'Snabb-tutorial',
        emoji: '🎓',
        hook: 'Lär dig detta på 60s',
        virality: 87,
        struktur: ['Resultat', 'Steg 1', 'Steg 2', 'Steg 3']
    },
    'opopular-asikt': {
        namn: 'Opopulär åsikt',
        emoji: '🌶️',
        hook: 'Detta är kontroversiellt...',
        virality: 96,
        struktur: ['Åsikt', 'Argument', 'Motargument', 'Slutsats']
    },
    'life-hack': {
        namn: 'Life Hack',
        emoji: '💡',
        hook: 'Detta sparar 10h/vecka',
        virality: 89,
        struktur: ['Problem', 'Hack', 'Demonstration', 'Resultat']
    },
    'framtids-tips': {
        namn: 'Framtids-tips',
        emoji: '🔮',
        hook: 'Detta händer 2025...',
        virality: 85,
        struktur: ['Trend', 'Förutsägelse', 'Förberedelse', 'Action']
    }
};

// ==========================================
// INITIERING
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM redo - initierar...');
    
    initFormatVal();
    initAutoGenerera();
    initSkapaPaket();
    initLaddaSparat();
});

// ==========================================
// 1. FORMAT-VAL (12 mallar)
// ==========================================

function initFormatVal() {
    const formatCards = document.querySelectorAll('.format-card, [data-format]');
    
    console.log(`Hittade ${formatCards.length} format-kort`);
    
    formatCards.forEach(card => {
        card.addEventListener('click', function() {
            // Ta bort aktiv från alla
            formatCards.forEach(c => {
                c.classList.remove('active', 'selected');
                c.style.border = '';
                c.style.transform = '';
            });
            
            // Markera denna som aktiv
            this.classList.add('active', 'selected');
            this.style.border = '3px solid #3b82f6';
            this.style.transform = 'scale(1.05)';
            
            // Spara valet
            valtFormat = this.dataset.format;
            valtFormatData = formatData[valtFormat];
            
            localStorage.setItem('viralFormat', valtFormat);
            
            console.log('✅ Valt format:', valtFormat);
            
            // Visa bekräftelse
            visaToast(`Valt: ${valtFormatData ? valtFormatData.namn : valtFormat}`);
        });
    });
}

// ==========================================
// 2. AUTO-GENERERA BILDBESKRIVNINGAR
// ==========================================

function initAutoGenerera() {
    const generateBtn = document.querySelector('#generate-btn, .generate-btn, [data-action="generate"]');
    const keywordsInput = document.querySelector('#keywords, input[placeholder*="nyckelord"], input[placeholder*="ämne"]');
    
    if (generateBtn) {
        console.log('✅ Hittade generera-knapp');
        
        generateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const keywords = keywordsInput ? keywordsInput.value : '';
            
            if (!keywords.trim()) {
                alert('📝 Fyll i nyckelord eller ämne först!');
                if (keywordsInput) keywordsInput.focus();
                return;
            }
            
            if (!valtFormat) {
                alert('🎬 Välj ett format från steg 1 först!');
                return;
            }
            
            genereraBildbeskrivningar(keywords);
        });
    } else {
        console.log('⚠️ Hittade ingen generera-knapp');
    }
}

function genereraBildbeskrivningar(keywords) {
    console.log('🎨 Genererar bildbeskrivningar för:', keywords);
    
    const format = valtFormatData || formatData['chockerande-fakta'];
    
    const bilder = [
        {
            typ: 'THUMBNAIL',
            beskrivning: `Närbild av ${keywords}, ${format.emoji} chockat ansiktsuttryck, röd pil/pekare, text-overlay "${format.hook}", hög kontrast, 9:16 format`
        },
        {
            typ: 'BILD 1',
            beskrivning: `${keywords} i action, dramatiskt ljus, ${format.struktur[0]}-scen, professionell kvalitet, vertikalt format`
        },
        {
            typ: 'BILD 2',
            beskrivning: `Detalj av ${keywords}, före/efter eller split-screen, fokus på ${format.struktur[1]}, estetisk bakgrund`
        }
    ];
    
    visaBildResultat(bilder);
    
    localStorage.setItem('viralKeywords', keywords);
    localStorage.setItem('viralBilder', JSON.stringify(bilder));
}

function visaBildResultat(bilder) {
    let outputDiv = document.querySelector('#bild-output, .bild-output, #image-result');
    
    if (!outputDiv) {
        outputDiv = document.createElement('div');
        outputDiv.id = 'bild-output';
        outputDiv.style.cssText = 'margin-top: 20px; padding: 20px; background: #1a1a2e; border-radius: 12px;';
        
        const inputSection = document.querySelector('#keywords, .keywords-section');
        if (inputSection && inputSection.parentNode) {
            inputSection.parentNode.appendChild(outputDiv);
        } else {
            document.body.appendChild(outputDiv);
        }
    }
    
    outputDiv.innerHTML = `
        <h3 style="color: #3b82f6; margin-bottom: 15px;">🎨 Genererade bildbeskrivningar</h3>
        ${bilder.map(b => `
            <div style="background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <strong style="color: #60a5fa;">${b.typ}</strong>
                <p style="margin: 8px 0 0 0; color: #e2e8f0;">${b.beskrivning}</p>
                <button onclick="kopieraText('${b.beskrivning.replace(/'/g, "\\'")}')" 
                        style="margin-top: 10px; padding: 6px 12px; background: #3b82f6; border: none; border-radius: 6px; color: white; cursor: pointer; font-size: 12px;">
                    📋 Kopiera
                </button>
            </div>
        `).join('')}
    `;
    
    visaToast('✅ Bildbeskrivningar genererade!');
}

// ==========================================
// 3. SKAPA VIRAL-PAKET
// ==========================================

function initSkapaPaket() {
    const allaKnappar = document.querySelectorAll('button');
    let skapaKnapp = null;
    
    allaKnappar.forEach(btn => {
        const text = btn.textContent.toLowerCase();
        if (text.includes('skapa') || text.includes('generera') || text.includes('klart') || text.includes('paket')) {
            skapaKnapp = btn;
        }
    });
    
    if (skapaKnapp) {
        console.log('✅ Hittade skapa-knapp:', skapaKnapp.textContent);
        
        skapaKnapp.addEventListener('click', function(e) {
            e.preventDefault();
            skapaViralPaket();
        });
    } else {
        console.log('⚠️ Hittade ingen skapa-knapp');
    }
}

function skapaViralPaket() {
    const keywords = localStorage.getItem('viralKeywords');
    
    if (!valtFormat) {
        alert('🎬 Välj ett format först! (Steg 1)');
        return;
    }
    
    if (!keywords) {
        alert('📝 Fyll i nyckelord och generera bildbeskrivningar först! (Steg 2)');
        return;
    }
    
    console.log('🎬 Skapar viral-paket:', valtFormat, keywords);
    
    const format = valtFormatData || formatData[valtFormat];
    
    const paket = {
        thumbnail: genereraThumbnail(format, keywords),
        bastaTid: analyseraBastaTid(),
        manus: genereraManus(format, keywords),
        storyboard: genereraStoryboard(format, keywords)
    };
    
    visaViralPaket(paket);
    sparaTillHistorik(paket);
}

function genereraThumbnail(format, keywords) {
    return {
        titel: `${format.emoji} ${format.hook}`,
        element: [
            'Chockat/nyfiket ansiktsuttryck',
            `${keywords} i fokus`,
            'Kontrasterande färger (röd/gul)',
            'Pil eller cirkel som pekar',
            'Kort text (max 3 ord)',
            '9:16 format (1080x1920)'
        ],
        farger: ['Röd (#ff0000)', 'Gul (#ffd700)', 'Svart (#000000)'],
        text: format.hook
    };
}

function analyseraBastaTid() {
    const tider = [
        { dag: 'Måndag', tid: '12:00', anledning: 'Lunchrast' },
        { dag: 'Tisdag', tid: '19:00', anledning: 'Efter jobbet' },
        { dag: 'Onsdag', tid: '12:00', anledning: 'Midvecka-break' },
        { dag: 'Torsdag', tid: '20:00', anledning: 'Nära helg' },
        { dag: 'Fredag', tid: '16:00', anledning: 'Helgkänsla' },
        { dag: 'Lördag', tid: '10:00', anledning: 'Morgon-scroll' },
        { dag: 'Söndag', tid: '20:00', anledning: 'Söndagsångest' }
    ];
    
    return tider[Math.floor(Math.random() * tider.length)];
}

function genereraManus(format, keywords) {
    const struktur = format.struktur;
    
    return {
        hook: `${format.emoji} ${format.hook}\n\n"Om du vill förstå ${keywords}, måste du se detta..."`,
        del1: `[${struktur[0]}]\nHär etablerar du ${keywords} och väcker nyfikenhet. Håll det kort, max 3 sekunder.`,
        del2: `[${struktur[1]}]\nUtveckla historien eller visa värdet. Detta är kärnan av din video.`,
        del3: `[${struktur[2]}]\nBygg upp till höjdpunkten. Använd dramatik eller överraskning.`,
        cta: `[${struktur[3]}]\nCall-to-action: "Följ för mer", "Spara detta", "Tagga en vän"\n\n#${keywords.replace(/\s+/g, '')} #viral #fyp #trending`,
        langd: '30-45 sekunder',
        ljud: 'Trendande ljud rekommenderas'
    };
}

function genereraStoryboard(format, keywords) {
    return [
        { sekund: '0-3', bild: 'Hook - chockat ansikte', text: 'Setup', ljud: 'Hook-ljud' },
        { sekund: '3-15', bild: `${keywords} introduktion`, text: 'Värde', ljud: 'Berättarröst' },
        { sekund: '15-30', bild: 'Detalj/fördjupning', text: 'Klimax', ljud: 'Musik bygger upp' },
        { sekund: '30-40', bild: 'Resultat/reveal', text: 'Payoff', ljud: 'Drop/climax' },
        { sekund: '40-45', bild: 'CTA-skärm', text: 'Följ + Spara', ljud: 'Avslutande ljud' }
    ];
}

function visaViralPaket(paket) {
    let resultDiv = document.querySelector('#resultat, #result, .resultat-sektion, #viral-result');
    
    if (!resultDiv) {
        resultDiv = document.createElement('div');
        resultDiv.id = 'viral-result';
        resultDiv.style.cssText = 'margin: 30px auto; max-width: 800px; padding: 20px;';
        document.body.appendChild(resultDiv);
    }
    
    resultDiv.innerHTML = `
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px; border-radius: 16px; border: 2px solid #3b82f6;">
            <h2 style="color: #3b82f6; text-align: center; margin-bottom: 25px;">🎬 DITT VIRAL-PAKET ÄR KLART!</h2>
            
            <div style="background: #0f172a; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #60a5fa; margin-bottom: 15px;">🎯 THUMBNAIL</h3>
                <p><strong>${paket.thumbnail.titel}</strong></p>
                <ul style="color: #cbd5e1; margin: 10px 0;">
                    ${paket.thumbnail.element.map(e => `<li>${e}</li>`).join('')}
                </ul>
                <p style="color: #94a3b8; font-size: 14px;">Färger: ${paket.thumbnail.farger.join(', ')}</p>
            </div>
            
            <div style="background: #0f172a; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #60a5fa; margin-bottom: 15px;">⏰ BÄSTA TID ATT POSTA</h3>
                <p style="font-size: 24px; color: #3b82f6; font-weight: bold;">
                    ${paket.bastaTid.dag} kl ${paket.bastaTid.tid}
                </p>
                <p style="color: #94a3b8;">${paket.bastaTid.anledning}</p>
            </div>
            
            <div style="background: #0f172a; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="color: #60a5fa; margin-bottom: 15px;">📝 MANUS</h3>
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; color: #e2e8f0; margin-bottom: 10px;">${paket.manus.hook}</div>
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; color: #e2e8f0; margin-bottom: 10px;">${paket.manus.del1}</div>
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; color: #e2e8f0; margin-bottom: 10px;">${paket.manus.del2}</div>
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; color: #e2e8f0; margin-bottom: 10px;">${paket.manus.del3}</div>
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; color: #e2e8f0; border: 2px solid #3b82f6;">${paket.manus.cta}</div>
                <p style="color: #94a3b8; margin-top: 10px;">⏱️ Längd: ${paket.manus.langd} | 🎵 ${paket.manus.ljud}</p>
            </div>
            
            <div style="background: #0f172a; padding: 20px; border-radius: 12px;">
                <h3 style="color: #60a5fa; margin-bottom: 15px;">🎬 STORYBOARD</h3>
                <div style="display: grid; gap: 10px;">
                    ${paket.storyboard.map(s => `
                        <div style="display: flex; gap: 15px; background: #1e293b; padding: 12px; border-radius: 8px; align-items: center;">
                            <span style="background: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">${s.sekund}</span>
                            <div style="flex: 1;">
                                <p style="margin: 0; color: #e2e8f0;"><strong>${s.bild}</strong></p>
                                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">${s.text} | 🎵 ${s.ljud}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div style="margin-top: 25px; display: flex; gap: 10px; flex-wrap: wrap;">
                <button onclick="kopieraHelaPaketet()" style="flex: 1; min-width: 200px; padding: 15px; background: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                    📋 Kopiera allt
                </button>
                <button onclick="sparaSomFil()" style="flex: 1; min-width: 200px; padding: 15px; background: #10b981; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                    💾 Spara som fil
                </button>
            </div>
        </div>
    `;
    
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    visaToast('🎉 Viral-paket skapat!');
}

// ==========================================
// HJÄLPFUNKTIONER
// ==========================================

function kopieraText(text) {
    navigator.clipboard.writeText(text).then(() => {
        visaToast('📋 Kopierat!');
    });
}

function kopieraHelaPaketet() {
    const resultDiv = document.querySelector('#viral-result');
    if (resultDiv) {
        const text = resultDiv.innerText;
        navigator.clipboard.writeText(text).then(() => {
            visaToast('📋 Hela paketet kopierat!');
        });
    }
}

function sparaSomFil() {
    const resultDiv = document.querySelector('#viral-result');
    if (!resultDiv) return;
    
    const text = resultDiv.innerText;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `viral-paket-${valtFormat}-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    visaToast('💾 Fil sparad!');
}

function visaToast(meddelande) {
    const gammal = document.querySelector('.toast');
    if (gammal) gammal.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = meddelande;
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: #3b82f6;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        z-index: 10000;
        animation: slideUp 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function sparaTillHistorik(paket) {
    let historik = JSON.parse(localStorage.getItem('viralHistorik') || '[]');
    historik.unshift({
        datum: new Date().toISOString(),
        format: valtFormat,
        paket: paket
    });
    historik = historik.slice(0, 10);
    localStorage.setItem('viralHistorik', JSON.stringify(historik));
}

function initLaddaSparat() {
    const sparatFormat = localStorage.getItem('viralFormat');
    if (sparatFormat) {
        const card = document.querySelector(`[data-format="${sparatFormat}"]`);
        if (card) {
            setTimeout(() => card.click(), 100);
        }
    }
}

// CSS-animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
`;
document.head.appendChild(style);
