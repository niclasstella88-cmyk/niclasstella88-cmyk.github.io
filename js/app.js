function generateContent() {
    const topic = document.getElementById('topic').value.trim();
    const output = document.getElementById('outputArea');
    
    if (!topic) {
        output.innerHTML = '<p style="color:#ff4444;text-align:center;">⛔ Skriv ett ämne först!</p>';
        return;
    }
    
    const hooks = [
        "3 saker jag önskar jag visste om " + topic + " innan jag började...",
        "Ingen pratar om detta när det kommer till " + topic,
        "Varför 95% misslyckas med " + topic + " (och hur du undviker det)",
        "Det här förändrade allt för mig inom " + topic,
        "Myten om " + topic + " som alla tror på"
    ];
    
    const bodies = [
        "För 3 år sedan trodde jag att " + topic + " var lätt. Jag hade fel. Det handlar egentligen om att vara konsekvent.\n\nHär är mina 3 bästa tips:",
        "Jag spenderade 50,000 kr på att lära mig " + topic + ". Spara pengarna och gör så här istället:\n\nSteg 1: Fokusera på grunderna\nSteg 2: Testa olika format\nSteg 3: Mät dina resultat",
        "Stop! Innan du provar " + topic + ", läs detta. Jag har testat allt så du slipper göra misstagen."
    ];
    
    const ctas = [
        "Följ för mer om " + topic + " 👆",
        "Spara detta till senare 💾", 
        "Tagga någon som behöver se detta 👇",
        "Kommentera 'GUIDE' så skickar jag min checklista"
    ];
    
    const hashtags = "#svensktiktok #företag #tips #" + topic.replace(/\s+/g, '').toLowerCase();
    
    const hook = hooks[Math.floor(Math.random() * hooks.length)];
    const body = bodies[Math.floor(Math.random() * bodies.length)];
    const cta = ctas[Math.floor(Math.random() * ctas.length)];
    const views = Math.floor(Math.random() * 50000) + 10000;
    const likes = Math.floor(views * (0.05 + Math.random() * 0.1));
    
    const fullScript = hook + "\n\n" + body + "\n\n" + cta + "\n\n" + hashtags;
    
    output.innerHTML = `
        <div class="content-result">
            <h4>✨ AI-GENERERAT MANUS</h4>
            <div class="script">
                <strong style="color:#fff;font-size:1.1rem;">${hook}</strong><br><br>
                ${body.replace(/\n/g, '<br>')}<br><br>
                <strong style="color:#00D4FF;">${cta}</strong><br><br>
                <span style="color:#00D4FF;">${hashtags}</span>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <strong>${views.toLocaleString()}</strong>
                    <span>Beräknade visningar</span>
                </div>
                <div class="metric">
                    <strong>${likes.toLocaleString()}</strong>
                    <span>Uppskattade likes</span>
                </div>
                <div class="metric">
                    <strong>45s</strong>
                    <span>Rekommenderad längd</span>
                </div>
            </div>
            
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:15px;">
                <button onclick="copyScript()" class="btn" style="flex:1;min-width:120px;">📋 Kopiera manus</button>
                <button onclick="alert('Sparat!')" class="btn" style="flex:1;min-width:120px;background:#1E1E2E;">💾 Spara</button>
            </div>
            
            <div style="background:rgba(0,102,255,0.1);padding:15px;border-radius:8px;border-left:3px solid var(--primary);font-size:0.9rem;color:var(--text2);">
                💡 <strong>Proffstips:</strong> Publicera mellan 18:00-20:00 för maximal räckvidd i din nisch.
            </div>
        </div>
    `;
    
    window.currentScript = fullScript;
}

function copyScript() {
    if (window.currentScript) {
        navigator.clipboard.writeText(window.currentScript).then(() => {
            alert('✅ Manus kopierat till urklipp!');
        }).catch(() => {
            alert('Kunde inte kopiera automatiskt. Markera och kopiera manuellt.');
        });
    }
}

// Enter-knappen fungerar också
document.getElementById('topic').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') generateContent();
});
