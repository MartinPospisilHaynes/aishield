/**
 * AIshield.cz — Compliance Widget (Web Component)
 * Vanilla JS, Shadow DOM, <3 KB gzipped.
 * 
 * Vložení na web klienta:
 *   <script src="https://api.aishield.cz/api/widget/COMPANY_ID/bundle.js" defer></script>
 *   <aishield-widget company-id="COMPANY_ID"></aishield-widget>
 * 
 * Nebo jednořádkově:
 *   <script src="https://api.aishield.cz/api/widget/COMPANY_ID/bundle.js" defer></script>
 *
 * GDPR: Nepotřebuje cookie souhlas (je informační, neprofiluje).
 * CSP:  script-src https://api.aishield.cz; connect-src https://api.aishield.cz;
 */

(function () {
    'use strict';

    var API_BASE = 'https://api.aishield.cz/api/widget';

    // ── Auto-detect company ID from script src ──
    var scripts = document.querySelectorAll('script[src*="aishield"]');
    var autoCompanyId = null;
    for (var i = 0; i < scripts.length; i++) {
        var m = scripts[i].src.match(/widget\/([^\/]+)\/bundle/);
        if (m) { autoCompanyId = m[1]; break; }
    }

    // ── Chatbot Detection ──
    var CHATBOT_SELECTORS = [
        '#intercom-frame', '#intercom-container', 'iframe[name="intercom-messenger-frame"]',
        '.tidio-chat', '#tidio-chat', '#tidio-chat-iframe',
        '#launcher', '.zEWidget-launcher', 'iframe[data-product="web_widget"]',
        '#drift-widget', '#drift-frame-controller',
        '#hubspot-messages-iframe-container', '#hs-chat-open',
        '.crisp-client', '#crisp-chatbox',
        '#smartsupp-widget-container', '#chat-application',
        'iframe[src*="livechatinc"]', '#chat-widget-container',
        '.fb-customerchat', '.fb_dialog',
        '[data-testid="widget_container"]',
    ];

    function detectChatbots() {
        var found = [];
        for (var i = 0; i < CHATBOT_SELECTORS.length; i++) {
            if (document.querySelector(CHATBOT_SELECTORS[i])) {
                found.push(CHATBOT_SELECTORS[i]);
            }
        }
        return found;
    }

    // ── Web Component ──
    class AIShieldWidget extends HTMLElement {
        constructor() {
            super();
            this._shadow = this.attachShadow({ mode: 'open' });
            this._expanded = false;
        }

        connectedCallback() {
            var companyId = this.getAttribute('company-id') || autoCompanyId;
            if (!companyId) {
                console.warn('AIshield widget: missing company-id');
                return;
            }
            this._companyId = companyId;
            this._render();
            this._loadConfig();
        }

        _render() {
            this._shadow.innerHTML = '' +
                '<style>' +
                ':host{position:fixed;bottom:20px;right:20px;z-index:2147483647;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:13px;line-height:1.4;}' +
                '.badge{background:#0f172a;border:1px solid rgba(232,121,249,0.3);border-radius:12px;padding:10px 14px;color:#f1f5f9;box-shadow:0 4px 24px rgba(0,0,0,0.4);cursor:pointer;max-width:280px;transition:all .3s ease;}' +
                '.badge:hover{border-color:rgba(232,121,249,0.6);box-shadow:0 4px 28px rgba(232,121,249,0.15);}' +
                '.header{display:flex;align-items:center;gap:6px;}' +
                '.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}' +
                '.brand{font-weight:800;letter-spacing:-0.03em;}' +
                '.brand-ai{color:#f1f5f9;}' +
                '.brand-shield{background:linear-gradient(135deg,#e879f9,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}' +
                '.info{color:#94a3b8;font-size:11px;margin-top:4px;}' +
                '.expanded{margin-top:8px;border-top:1px solid rgba(255,255,255,0.08);padding-top:8px;display:none;}' +
                '.expanded.show{display:block;}' +
                '.system{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px;color:#cbd5e1;}' +
                '.system .sdot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}' +
                '.high{background:#ef4444;}.limited{background:#f59e0b;}.minimal{background:#22c55e;}.compliant{background:#22c55e;}.at_risk{background:#f59e0b;}.non_compliant{background:#ef4444;}.no_data{background:#64748b;}' +
                '.link{display:block;margin-top:6px;color:#e879f9;text-decoration:none;font-size:11px;}' +
                '.link:hover{text-decoration:underline;}' +
                '.chatbot-label{position:fixed;bottom:80px;right:80px;background:#0f172a;border:1px solid rgba(245,158,11,0.4);border-radius:8px;padding:6px 10px;color:#f59e0b;font-size:10px;z-index:2147483646;pointer-events:none;opacity:0;transition:opacity .3s;}' +
                '.chatbot-label.visible{opacity:1;}' +
                '</style>' +
                '<div class="badge" id="badge">' +
                '<div class="header">' +
                '<span class="dot" id="dot"></span>' +
                '<span class="brand"><span class="brand-ai">AI</span><span class="brand-shield">shield</span></span>' +
                '</div>' +
                '<div class="info" id="info">Načítání...</div>' +
                '<div class="expanded" id="details"></div>' +
                '</div>' +
                '<div class="chatbot-label" id="chatbot-label">🤖 AI chatbot</div>';

            this._shadow.getElementById('badge').addEventListener('click', this._toggle.bind(this));
        }

        _toggle() {
            this._expanded = !this._expanded;
            var details = this._shadow.getElementById('details');
            if (this._expanded) {
                details.classList.add('show');
            } else {
                details.classList.remove('show');
            }
        }

        _loadConfig() {
            var self = this;
            fetch(API_BASE + '/' + this._companyId + '/config')
                .then(function (r) { return r.json(); })
                .then(function (cfg) { self._applyConfig(cfg); })
                .catch(function (e) { console.log('AIshield widget error:', e); });
        }

        _applyConfig(cfg) {
            if (!cfg.display || !cfg.display.show_badge) {
                this.style.display = 'none';
                return;
            }

            // Status dot color
            var dot = this._shadow.getElementById('dot');
            var status = cfg.compliance ? cfg.compliance.status : 'no_data';
            dot.className = 'dot ' + status;

            // Info text
            var info = this._shadow.getElementById('info');
            info.textContent = cfg.display.badge_text || (cfg.total_ai_systems + ' AI systémů detekováno');

            // Banner
            if (cfg.display.banner) {
                info.textContent += ' — ' + cfg.display.banner;
            }

            // Expanded details
            var details = this._shadow.getElementById('details');
            var html = '';

            if (cfg.ai_systems && cfg.ai_systems.length > 0) {
                for (var i = 0; i < Math.min(cfg.ai_systems.length, 6); i++) {
                    var sys = cfg.ai_systems[i];
                    var risk = sys.risk_level || 'minimal';
                    html += '<div class="system"><span class="sdot ' + risk + '"></span>' +
                        sys.name + ' — ' + (sys.article || '') + '</div>';
                }
                if (cfg.ai_systems.length > 6) {
                    html += '<div class="system" style="color:#64748b;">+ dalších ' + (cfg.ai_systems.length - 6) + ' systémů</div>';
                }
            }

            // Compliance deadline
            if (cfg.compliance && cfg.compliance.days_remaining > 0) {
                html += '<div class="system" style="color:#f59e0b;">⏱ Do AI Act deadline: ' + cfg.compliance.days_remaining + ' dní</div>';
            }

            // Transparency page link
            html += '<a class="link" href="/ai-transparence" target="_blank">Více o AI na tomto webu →</a>';

            details.innerHTML = html;

            // Chatbot detection
            var chatbots = detectChatbots();
            if (chatbots.length > 0) {
                var label = this._shadow.getElementById('chatbot-label');
                label.classList.add('visible');
                // Position near chatbot widget
                setTimeout(function () { label.classList.remove('visible'); }, 8000);
            }
        }
    }

    // Register custom element
    if (!customElements.get('aishield-widget')) {
        customElements.define('aishield-widget', AIShieldWidget);
    }

    // Auto-create widget if loaded via script tag with company ID
    if (autoCompanyId && !document.querySelector('aishield-widget')) {
        document.addEventListener('DOMContentLoaded', function () {
            var el = document.createElement('aishield-widget');
            el.setAttribute('company-id', autoCompanyId);
            document.body.appendChild(el);
        });
    }

})();
