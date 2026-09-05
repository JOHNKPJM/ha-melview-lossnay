class LossnayCardBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = {};
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error('Lossnay card requires entity: fan.your_lossnay');
    this._config = { maintenance: 'integrated', ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() { return 8; }

  getGridOptions() { return { columns: 5, rows: 'auto', min_columns: 4 }; }

  _state() { return this._hass?.states?.[this._config.entity]; }
  _a() { return this._state()?.attributes || {}; }
  _fmt(v, suffix = '') { return v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : `${Number(v).toFixed(1)}${suffix}`; }
  _days(days) {
    if (days === null || days === undefined) return '—';
    const d = Number(days);
    if (d < 0) return `${Math.abs(d)}d overdue`;
    if (d === 0) return 'Due today';
    if (d < 60) return `${d} days`;
    const months = Math.round(d / 30.44);
    if (months < 12) return `${months} months`;
    const years = Math.floor(months / 12), rem = months % 12;
    return rem ? `${years}y ${rem}m` : `${years} year${years === 1 ? '' : 's'}`;
  }

  async _service(domain, service, data = {}) {
    if (!this._hass) return;
    await this._hass.callService(domain, service, data);
  }

  _styles() {
    return `
      :host { display:block; --ln-bg:#101722; --ln-panel:#182230; --ln-panel2:#1d2938; --ln-border:rgba(255,255,255,.08); --ln-text:#f5f7fa; --ln-muted:#9ca8b6; --ln-blue:#20a7ff; --ln-blue2:#72d4ff; --ln-red:#ff5b45; --ln-orange:#ff9f2f; --ln-green:#42d392; --ln-yellow:#ffc857; font-family:var(--paper-font-body1_-_font-family,Inter,system-ui,sans-serif); }
      * { box-sizing:border-box; }
      ha-card { overflow:hidden; background:linear-gradient(145deg,#0e151f,#121b27 58%,#0e151f); color:var(--ln-text); border-radius:22px; box-shadow:0 10px 28px rgba(0,0,0,.24); container-type:inline-size; container-name:lossnay; }
      .wrap { padding:20px; }
      .header { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:16px; }
      .title { font-size:24px; font-weight:700; letter-spacing:-.02em; }
      .subtitle { color:var(--ln-muted); font-size:12px; margin-top:3px; }
      .pill { padding:8px 12px; border-radius:999px; border:1px solid var(--ln-border); background:rgba(255,255,255,.035); color:var(--ln-muted); font-size:12px; }
      .grid-top { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(220px,.7fr); gap:14px; }
      .panel { background:linear-gradient(145deg,var(--ln-panel),#151e2b); border:1px solid var(--ln-border); border-radius:18px; padding:16px; }
      .panel-title { display:flex; align-items:center; gap:8px; font-size:16px; font-weight:650; margin-bottom:10px; }
      .core { min-height:240px; position:relative; overflow:hidden; }
      .core-labels { display:grid; grid-template-columns:1fr 1fr; gap:90px 28px; position:relative; z-index:2; }
      .air-label.right { text-align:right; }
      .air-name { color:var(--ln-muted); font-size:12px; }
      .air-value { font-size:20px; font-weight:700; margin-top:3px; }
      .svg-air { position:absolute; inset:58px 16px 20px; width:calc(100% - 32px); height:150px; z-index:1; }
      .hero { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:240px; text-align:center; }
      .hero-icon { width:48px; height:48px; display:grid; place-items:center; border-radius:50%; background:rgba(255,159,47,.12); color:var(--ln-orange); font-size:28px; margin-bottom:8px; }
      .hero-num { font-size:42px; font-weight:800; line-height:1; }
      .hero-label { color:var(--ln-orange); font-size:15px; font-weight:650; margin-top:8px; }
      .hero-sub { color:var(--ln-muted); font-size:12px; margin-top:6px; }
      .hero.cool .hero-icon,.hero.cool .hero-label { color:var(--ln-blue); } .hero.cool .hero-icon { background:rgba(32,167,255,.12); }
      .hero.warm .hero-icon,.hero.warm .hero-label { color:var(--ln-red); } .hero.warm .hero-icon { background:rgba(255,91,69,.12); }
      .controls { display:grid; grid-template-columns:.7fr 1.25fr 1.35fr; gap:14px; margin-top:14px; }
      .big-toggle { width:100%; min-height:104px; border:none; border-radius:16px; color:white; background:linear-gradient(145deg,#168edc,#126da9); cursor:pointer; font-size:16px; font-weight:700; }
      .big-toggle.off { background:linear-gradient(145deg,#293646,#202b38); color:#c6cfda; }
      .seg { display:grid; gap:8px; } .seg.modes { grid-template-columns:repeat(3,1fr); } .seg.speeds { grid-template-columns:repeat(5,1fr); }
      .btn { border:1px solid var(--ln-border); background:#202b39; color:#cbd4de; min-height:46px; border-radius:12px; cursor:pointer; font-size:12px; font-weight:650; padding:7px; }
      .btn.active { border-color:rgba(32,167,255,.6); background:linear-gradient(145deg,#168edc,#106ba8); color:white; box-shadow:0 0 0 1px rgba(32,167,255,.15) inset; }
      .section-head { color:var(--ln-muted); font-size:11px; text-transform:uppercase; letter-spacing:.08em; margin-bottom:9px; }
      .temps { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:14px; }
      .temp { background:#17212e; border:1px solid var(--ln-border); border-radius:15px; padding:13px; text-align:center; }
      .temp .name { color:var(--ln-muted); font-size:11px; min-height:28px; } .temp .val { font-size:18px; font-weight:750; margin-top:5px; }
      .temp.na .val { color:#718096; }
      .maintenance { margin-top:14px; }
      .maint-top { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:12px; }
      .maint-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
      .maint-item { background:#17212e; border:1px solid var(--ln-border); border-radius:15px; padding:13px; }
      .maint-name { font-weight:650; font-size:13px; } .maint-due { font-size:19px; font-weight:750; margin:6px 0 2px; }
      .maint-meta { color:var(--ln-muted); font-size:11px; }
      .status-ok { color:var(--ln-green); } .status-soon { color:var(--ln-yellow); } .status-due { color:var(--ln-red); }
      .maint-actions { display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }
      .mini { border:1px solid var(--ln-border); background:#212d3b; color:#d7dee7; border-radius:9px; padding:6px 9px; cursor:pointer; font-size:11px; }
      .interval { display:flex; align-items:center; gap:6px; margin-top:9px; color:var(--ln-muted); font-size:11px; }
      .interval strong { color:#dce3eb; min-width:48px; text-align:center; }
      .footer { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:14px; }
      .foot { background:#17212e; border:1px solid var(--ln-border); border-radius:14px; padding:12px; color:var(--ln-muted); font-size:12px; text-align:center; }
      /* Responsive to the card's actual HA grid width, not the browser viewport. */
      @container lossnay (max-width: 620px) {
        .wrap { padding:14px; }
        .header { margin-bottom:12px; gap:10px; }
        .title { font-size:21px; }
        .pill { padding:6px 9px; }
        .grid-top { grid-template-columns:1fr; gap:10px; }
        .panel { border-radius:15px; padding:12px; }
        .core { min-height:210px; }
        .panel-title { font-size:14px; margin-bottom:8px; }
        .core-labels { gap:62px 16px; }
        .air-name { font-size:11px; }
        .air-value { font-size:18px; }
        .svg-air { inset:52px 10px 14px; width:calc(100% - 20px); height:132px; }
        .hero { min-height:98px; display:grid; grid-template-columns:42px auto 1fr; grid-template-rows:auto auto; column-gap:10px; row-gap:2px; text-align:left; justify-content:stretch; align-items:center; }
        .hero-icon { width:38px; height:38px; font-size:21px; margin:0; grid-row:1 / span 2; }
        .hero-num { font-size:34px; grid-row:1 / span 2; }
        .hero-label { margin:0; font-size:13px; align-self:end; }
        .hero-sub { margin:0; font-size:11px; align-self:start; }
        .controls { grid-template-columns:82px minmax(0,1fr); gap:10px; margin-top:10px; }
        .controls > .panel:nth-child(3) { grid-column:1 / -1; }
        .big-toggle { min-height:76px; padding:6px; font-size:13px; line-height:1.15; }
        .section-head { font-size:10px; margin-bottom:7px; }
        .seg { gap:5px; }
        .seg.modes { grid-template-columns:repeat(3,minmax(0,1fr)); }
        .seg.speeds { grid-template-columns:repeat(5,minmax(0,1fr)); }
        .btn { min-width:0; min-height:42px; padding:5px 3px; font-size:10.5px; border-radius:10px; overflow:hidden; }
        .temps { grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:10px; }
        .temp { padding:10px 7px; border-radius:12px; }
        .temp .name { min-height:0; font-size:10px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .temp .val { font-size:16px; }
        .maintenance { margin-top:10px; }
        .maint-top { margin-bottom:8px; }
        .maint-grid { grid-template-columns:1fr; gap:7px; }
        .maint-item { display:grid; grid-template-columns:minmax(0,1fr) auto; column-gap:8px; padding:10px; }
        .maint-name { font-size:12px; }
        .maint-due { font-size:16px; margin:0; text-align:right; }
        .maint-meta, .maint-actions, .interval { grid-column:1 / -1; }
        .interval { margin-top:7px; }
        .maint-actions { margin-top:7px; }
        .footer { gap:6px; margin-top:10px; }
        .foot { padding:9px 5px; border-radius:11px; font-size:10px; }
      }
      @container lossnay (max-width: 420px) {
        .wrap { padding:11px; }
        .core { min-height:198px; }
        .core-labels { gap:56px 10px; }
        .air-value { font-size:17px; }
        .hero { grid-template-columns:36px auto 1fr; min-height:88px; }
        .hero-icon { width:34px; height:34px; font-size:19px; }
        .hero-num { font-size:30px; }
        .controls { grid-template-columns:72px minmax(0,1fr); gap:7px; }
        .btn { font-size:9.5px; }
      }
      @media(max-width:780px){ .maint-grid{grid-template-columns:1fr} }
    `;
  }

  _airSvg(attrs) {
    const fresh = Number(attrs.fresh_air_in), stale = Number(attrs.stale_air_out);
    const bypass = attrs.airflow_state === 'Bypass';
    const outsideCooler = Number.isFinite(fresh) && Number.isFinite(stale) ? fresh < stale : true;
    const inColor = outsideCooler ? '#20a7ff' : '#ff5b45';
    const outColor = outsideCooler ? '#ff5b45' : '#20a7ff';
    if (bypass) {
      return `<svg class="svg-air" viewBox="0 0 520 150" preserveAspectRatio="none">
        <defs><marker id="arrIn" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="${inColor}"/></marker><marker id="arrOut" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="${outColor}"/></marker></defs>
        <path d="M42 108 C165 108,350 108,478 108" fill="none" stroke="${inColor}" stroke-width="10" stroke-linecap="round" marker-end="url(#arrIn)"/>
        <path d="M478 42 C350 42,165 42,42 42" fill="none" stroke="${outColor}" stroke-width="10" stroke-linecap="round" marker-end="url(#arrOut)"/>
      </svg>`;
    }
    return `<svg class="svg-air" viewBox="0 0 520 150" preserveAspectRatio="none">
      <defs>
        <linearGradient id="freshGrad" x1="0" x2="1"><stop offset="0" stop-color="${inColor}"/><stop offset="1" stop-color="#ff8a4f"/></linearGradient>
        <linearGradient id="staleGrad" x1="1" x2="0"><stop offset="0" stop-color="${outColor}"/><stop offset="1" stop-color="#56bfff"/></linearGradient>
        <marker id="arrA" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#ff8a4f"/></marker>
        <marker id="arrB" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#56bfff"/></marker>
      </defs>
      <path d="M42 38 C190 38,330 112,478 112" fill="none" stroke="url(#freshGrad)" stroke-width="10" stroke-linecap="round" marker-end="url(#arrA)"/>
      <path d="M478 38 C330 38,190 112,42 112" fill="none" stroke="url(#staleGrad)" stroke-width="10" stroke-linecap="round" marker-end="url(#arrB)"/>
    </svg>`;
  }

  _maintStatusClass(status) {
    if (status === 'Overdue' || status === 'Due') return 'status-due';
    if (status === 'Due soon') return 'status-soon';
    return 'status-ok';
  }

  _maintenanceHtml(attrs, standalone = false) {
    const m = attrs.maintenance || {};
    if (!m.enabled) {
      return `<div class="panel maintenance"><div class="maint-top"><div><div class="panel-title">🛠 Maintenance</div><div class="subtitle">Optional local reminders for filters and Lossnay core</div></div><button class="btn active" data-maint-enable="1">Enable tracking</button></div></div>`;
    }
    const items = [
      ['wash','Wash filters','🧹',m.wash_interval_months,1],
      ['replace','Replace filters','♻️',m.replace_interval_months,12],
      ['core','Inspect / clean core','⬡',m.core_interval_months,12],
    ];
    const cards = items.map(([key,name,icon,months,step]) => {
      const status=m[`${key}_status`], days=m[`${key}_days`], due=m[`${key}_due`];
      const cycles = key === 'wash' ? `<div class="maint-meta">Washes since replacement: ${m.washes_since_replacement ?? 0} / 3</div>` : '';
      const unit = months >= 12 && months % 12 === 0 ? `${months/12} year${months===12?'':'s'}` : `${months} months`;
      return `<div class="maint-item">
        <div class="maint-name">${icon} ${name}</div>
        <div class="maint-due ${this._maintStatusClass(status)}">${this._days(days)}</div>
        <div class="maint-meta">Due ${due || '—'} · ${status || 'Unknown'}</div>${cycles}
        <div class="interval"><span>Interval</span><button class="mini" data-maint-adjust="${key}" data-delta="-${step}">−</button><strong>${unit}</strong><button class="mini" data-maint-adjust="${key}" data-delta="${step}">+</button></div>
        <div class="maint-actions"><button class="mini" data-maint-done="${key}">${key==='wash'?'Mark washed':key==='replace'?'Mark replaced':'Mark cleaned'}</button></div>
      </div>`;
    }).join('');
    return `<div class="panel maintenance"><div class="maint-top"><div><div class="panel-title">🛠 Lossnay Maintenance</div><div class="subtitle">User-managed reminders — independent of Melview</div></div><button class="mini" data-maint-enable="0">Disable</button></div><div class="maint-grid">${cards}</div></div>`;
  }

  _bindCommon(root, attrs) {
    root.querySelectorAll('[data-power]').forEach(el => el.onclick = () => this._service('fan', attrs.power_on ? 'turn_off' : 'turn_on', { entity_id: this._config.entity }));
    root.querySelectorAll('[data-mode]').forEach(el => el.onclick = () => {
      const map={Lossnay:'MD1','Auto Lossnay':'MD3',Bypass:'MD7'};
      // Select entity is retained for compatibility; use custom integration command service when available.
      this._service('melview_lossnay','set_ventilation_mode',{unit_id:attrs.unit_id,mode:el.dataset.mode});
    });
    root.querySelectorAll('[data-speed]').forEach(el => el.onclick = () => {
      const speed=el.dataset.speed;
      if(speed==='Auto') this._service('fan','set_preset_mode',{entity_id:this._config.entity,preset_mode:'Auto'});
      else this._service('fan','set_percentage',{entity_id:this._config.entity,percentage:Number(speed)*25});
    });
    root.querySelectorAll('[data-maint-enable]').forEach(el => el.onclick = () => this._service('melview_lossnay','set_maintenance_enabled',{unit_id:attrs.unit_id,enabled:el.dataset.maintEnable==='1'}));
    root.querySelectorAll('[data-maint-done]').forEach(el => el.onclick = () => this._service('melview_lossnay','mark_maintenance_done',{unit_id:attrs.unit_id,item:el.dataset.maintDone}));
    root.querySelectorAll('[data-maint-adjust]').forEach(el => el.onclick = () => {
      const m=attrs.maintenance||{}, key=el.dataset.maintAdjust, delta=Number(el.dataset.delta);
      const current=Number(m[`${key}_interval_months`]);
      this._service('melview_lossnay','set_maintenance_interval',{unit_id:attrs.unit_id,item:key,months:current+delta});
    });
  }
}

class LossnayCard extends LossnayCardBase {
  _render() {
    if (!this.shadowRoot || !this._config) return;
    const st=this._state();
    if(!st){ this.shadowRoot.innerHTML=`<style>${this._styles()}</style><ha-card><div class="wrap">Entity not found: ${this._config.entity||''}</div></ha-card>`; return; }
    const a={...st.attributes,power_on:st.state==='on'};
    const mode=a.ventilation_mode||'Unknown', bypass=a.airflow_state==='Bypass';
    const speedName=a.fan_speed||'Auto';
    let hero;
    if(bypass){
      const effect=a.bypass_effect||'Bypass', delta=a.bypass_temperature_difference;
      const cls=effect==='Cooling'?'cool':effect==='Warming'?'warm':'';
      hero=`<div class="panel hero ${cls}"><div class="hero-icon">${effect==='Cooling'?'❄':effect==='Warming'?'♨':'↔'}</div><div class="hero-num">${this._fmt(delta,'°')}</div><div class="hero-label">${effect}</div><div class="hero-sub">Outside air ${effect==='Cooling'?'cooler':'warmer'} than indoors</div></div>`;
    } else {
      hero=`<div class="panel hero"><div class="hero-icon">♨</div><div class="hero-num">${a.heat_recovery_efficiency==null?'—':Math.round(a.heat_recovery_efficiency)+'%'}</div><div class="hero-label">Heat recovery efficiency</div><div class="hero-sub">Incoming air changed by ${this._fmt(a.incoming_air_temperature_change,'°C')}</div></div>`;
    }
    const maint=this._config.maintenance==='integrated' ? this._maintenanceHtml(a) : '';
    this.shadowRoot.innerHTML=`<style>${this._styles()}</style><ha-card><div class="wrap">
      <div class="header"><div><div class="title">Lossnay</div><div class="subtitle">${a.model||'LGH-35RVX3-E'} · ${mode}</div></div><div class="pill">${a.power_on?'● On':'○ Off'}</div></div>
      <div class="grid-top">
        <div class="panel core"><div class="panel-title">♻ Lossnay Core · ${bypass?'Bypass':'Heat recovery'}</div>
          <div class="core-labels">
            <div class="air-label"><div class="air-name">Fresh Air In</div><div class="air-value">${this._fmt(a.fresh_air_in,'°C')}</div></div>
            <div class="air-label right"><div class="air-name">Stale Air Out</div><div class="air-value">${this._fmt(a.stale_air_out,'°C')}</div></div>
            <div class="air-label"><div class="air-name">Exhaust Air</div><div class="air-value">${bypass?'—':this._fmt(a.exhaust_air,'°C')}</div></div>
            <div class="air-label right"><div class="air-name">Pre-warmed</div><div class="air-value">${bypass?'—':this._fmt(a.pre_warmed,'°C')}</div></div>
          </div>${this._airSvg(a)}
        </div>${hero}
      </div>
      <div class="controls">
        <div class="panel"><div class="section-head">Power</div><button class="big-toggle ${a.power_on?'':'off'}" data-power="1">${a.power_on?'⏻  Power On':'⏻  Power Off'}</button></div>
        <div class="panel"><div class="section-head">Ventilation mode</div><div class="seg modes">${['Lossnay','Auto Lossnay','Bypass'].map(x=>`<button class="btn ${mode===x?'active':''}" data-mode="${x}">${x==='Lossnay'?'♻':x==='Auto Lossnay'?'⟳':'↔'}<br>${x}</button>`).join('')}</div></div>
        <div class="panel"><div class="section-head">Fan speed</div><div class="seg speeds">${['1','2','3','4','Auto'].map(x=>`<button class="btn ${(speedName===`Speed ${x}`)||(x==='Auto'&&speedName==='Auto')?'active':''}" data-speed="${x}">${x==='Auto'?'Auto':`Speed ${x}`}</button>`).join('')}</div></div>
      </div>
      <div class="temps">${[
        ['Fresh Air In',a.fresh_air_in,false],['Stale Air Out',a.stale_air_out,false],['Exhaust Air',a.exhaust_air,bypass],['Pre-warmed',a.pre_warmed,bypass]
      ].map(([n,v,na])=>`<div class="temp ${na?'na':''}"><div class="name">${n}</div><div class="val">${na?'—':this._fmt(v,'°C')}</div></div>`).join('')}</div>
      ${maint}
      <div class="footer"><div class="foot">🗓 Home Assistant schedule</div><div class="foot">✓ Fault ${a.fault||'OK'}</div><div class="foot">ⓘ Device information</div></div>
    </div></ha-card>`;
    this._bindCommon(this.shadowRoot,a);
  }
}

class LossnayMaintenanceCard extends LossnayCardBase {
  _render(){
    if(!this.shadowRoot||!this._config)return;
    const st=this._state();
    if(!st){this.shadowRoot.innerHTML=`<style>${this._styles()}</style><ha-card><div class="wrap">Entity not found: ${this._config.entity||''}</div></ha-card>`;return;}
    const a={...st.attributes,power_on:st.state==='on'};
    this.shadowRoot.innerHTML=`<style>${this._styles()}</style><ha-card><div class="wrap"><div class="header"><div><div class="title">Lossnay Maintenance</div><div class="subtitle">Filters and heat-exchange core</div></div><div class="pill">Local reminders</div></div>${this._maintenanceHtml(a,true)}</div></ha-card>`;
    this._bindCommon(this.shadowRoot,a);
  }
}

customElements.define('lossnay-card', LossnayCard);
customElements.define('lossnay-maintenance-card', LossnayMaintenanceCard);
window.customCards = window.customCards || [];
window.customCards.push({type:'lossnay-card',name:'Lossnay',description:'Rich Lossnay ventilation controls and airflow visualization'});
window.customCards.push({type:'lossnay-maintenance-card',name:'Lossnay Maintenance',description:'Filter and core maintenance tracker'});
