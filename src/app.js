let data = window.__INDIA_HEADLINES__;

// --- DOM Elements ---
const elements = {
  timestamp: document.getElementById("timestamp"),
  statusBadge: document.getElementById("statusBadge"),
  dailyInsightSummary: document.getElementById("dailyInsightSummary"),
  mustKnowGrid: document.getElementById("mustKnowGrid"),
  mustKnowCount: document.getElementById("mustKnowCount"),
  allHeadlinesCount: document.getElementById("allHeadlinesCount"),
  headlineGrid: document.getElementById("headlineGrid"),
  topicChips: document.getElementById("topicChips"),
  searchInput: document.getElementById("searchInput"),
  sourceHealthSummaryDisclosure: document.getElementById("sourceHealthSummaryDisclosure"),
  sourceHealthList: document.getElementById("sourceHealthList"),
  editionSelect: document.getElementById("editionSelect"),
  prevEditionBtn: document.getElementById("prevEditionBtn"),
  nextEditionBtn: document.getElementById("nextEditionBtn"),
};

// --- Utilities ---
const formatDateTime = (value) =>
  new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Kolkata"
  }).format(new Date(value));

const titleCase = (value) =>
  (value || "unknown")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const escapeHtml = (text) =>
  (text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

let glossaryMap = null;
let glossaryRegex = null;

async function loadGlossary() {
  try {
    const resp = await fetch('../assets/data/glossary.json');
    if (!resp.ok) return;
    const gdata = await resp.json();
    glossaryMap = new Map();
    const terms = [];
    for (const entry of gdata.terms) {
      glossaryMap.set(entry.term.toLowerCase(), entry.def);
      terms.push(entry.term);
    }
    terms.sort((a, b) => b.length - a.length);
    const escaped = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    glossaryRegex = new RegExp(`\\b(${escaped.join('|')})\\b`, 'g');
  } catch { /* glossary is optional — degrade silently */ }
}

function applyGlossary(text) {
  const safe = escapeHtml(text);
  if (!glossaryMap || !glossaryRegex) return safe;
  glossaryRegex.lastIndex = 0;
  return safe.replace(glossaryRegex, (match) => {
    const def = glossaryMap.get(match.toLowerCase());
    if (!def) return match;
    const safeDef = def.replace(/"/g, '&quot;');
    return `<abbr class="gloss-term" data-def="${safeDef}">${match}</abbr>`;
  });
}

const renderFacts = (facts) => {
  if (!facts || !facts.length) return '';
  const chips = facts
    .map(f => `<span class="fact-chip fact-chip--${f.type}" title="${f.type}">${f.text}</span>`)
    .join('');
  return `<div class="fact-chips">${chips}</div>`;
};

const renderStoryThread = (h) => {
  if (!h.storyDayCount || h.storyDayCount < 2) return '';
  const links = (h.storyEditions || []).map(e => {
    const label = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata' }).format(new Date(e.date));
    return `<li><a href="${e.url}" target="_blank" rel="noreferrer">${label} — ${escapeHtml(e.title)}</a></li>`;
  }).join('');
  return `<details class="story-thread">
    <summary class="story-thread-badge">Ongoing &middot; Day ${h.storyDayCount}</summary>
    <ul class="story-thread-panel">${links}</ul>
  </details>`;
};

// --- Rule-based Relevance ---
const rules = [
  {
    keywords: [
      'court', 'supreme court', 'high court', 'election commission', 'parliament',
      'lok sabha', 'rajya sabha', 'bill', 'law', 'policy', 'governor', 'federal',
      'constitutional', 'constitution', 'illegal', 'bribery', 'corruption', 'scam',
      'chief minister', 'deputy cm', 'minister', 'ministers', 'ministry', 'cabinet',
      'mla', 'mlas', 'election', 'electoral', 'bypoll', 'bypolls', 'voter', 'polling',
      'ordinance', 'amendment', 'panchayat', 'municipality', 'gram sabha', 'assembly',
      'president', 'prime minister', 'rti', 'right to information', 'cag', 'cbi',
      'enforcement directorate', 'lokpal', 'tribunal', 'verdict', 'judgment', 'chargesheet',
      'conviction', 'acquittal', 'legislature', 'governance', 'vigilance',
    ],
    tags: ['Polity', 'Governance'], gs: 'GS2', use: 'Mains',
    reason: 'covers constitutional, electoral, and state governance themes central to GS2.',
  },
  {
    keywords: [
      'rbi', 'inflation', 'gdp', 'trade', 'exports', 'budget', 'tax', 'jobs', 'economy',
      'paddy', 'wheat', 'procurement', 'msp', 'farmer', 'farmers', 'agriculture',
      'agricultural', 'crop', 'crops', 'harvest', 'kisan', 'rural development',
      'bank', 'banking', 'repo rate', 'monetary policy', 'fiscal', 'revenue', 'subsidy',
      'fdi', 'investment', 'stock market', 'sebi', 'nabard', 'insurance', 'pension',
      'manufacturing', 'industrial', 'infrastructure', 'startup', 'fintech',
      'unemployment', 'employment', 'wages', 'income', 'scheme', 'yojana', 'mgnrega',
      'food security', 'ration', 'pds', 'public distribution', 'niti aayog',
      'economic survey', 'import', 'tariff', 'msme', 'logistics', 'port', 'railway',
    ],
    tags: ['Economy'], gs: 'GS3', use: 'Mains',
    reason: 'connects agriculture, banking, fiscal policy, and economic governance themes.',
  },
  {
    keywords: [
      'climate', 'pollution', 'forest', 'wildlife', 'heatwave', 'decarbonisation',
      'renewable', 'river', 'solar', 'wind energy', 'carbon', 'emission', 'greenhouse',
      'deforestation', 'afforestation', 'biodiversity', 'species', 'endangered',
      'wetland', 'coral', 'ocean', 'marine', 'plastic', 'waste management',
      'flood', 'drought', 'cyclone', 'earthquake', 'glacier', 'landslide', 'monsoon',
      'national park', 'tiger', 'elephant', 'wildlife sanctuary', 'ecology', 'ecosystem',
      'net zero', 'unfccc', 'paris agreement', 'air quality', 'aqi', 'smog',
      'groundwater', 'water scarcity', 'disaster', 'ndrf',
    ],
    tags: ['Environment'], gs: 'GS3', use: 'Prelims',
    reason: 'relevant for conservation, climate action, and disaster management themes.',
  },
  {
    keywords: [
      'labour', 'migrant', 'caste', 'women', 'education', 'health', 'poverty',
      'vulnerable groups', 'substance abuse', 'dalit', 'tribal', 'tribe', 'adivasi',
      'obc', 'reservation', 'backward class', 'minority', 'gender', 'domestic violence',
      'trafficking', 'bonded labour', 'malnutrition', 'hunger', 'nutrition',
      'sanitation', 'disability', 'social security', 'welfare', 'human rights', 'nhrc',
      'communal', 'communalism', 'discrimination', 'child labour', 'maternal health',
      'infant mortality', 'literacy', 'school dropout', 'hygiene', 'ncpcr',
      'nutrient', 'nutrients', 'fortified', 'anaemia', 'stunting', 'wasting',
    ],
    tags: ['Society', 'Social Justice'], gs: 'GS1/GS2', use: 'Mains',
    reason: 'covers key social issues, welfare dimensions, and justice themes.',
  },
  {
    keywords: [
      'diplomacy', 'border', 'west asia', 'china', 'pakistan', 'treaty', 'global',
      'peace talks', 'india-china', 'india-us', 'india-pakistan', 'india-russia',
      'bilateral', 'multilateral', 'united nations', 'nato', 'quad', 'sco', 'brics',
      'asean', 'g20', 'g7', 'foreign minister', 'external affairs', 'foreign policy',
      'sanctions', 'geopolitical', 'south asia', 'southeast asia', 'middle east',
      'indo-pacific', 'imf', 'world bank', 'free trade agreement', 'fta',
      'ceasefire', 'humanitarian', 'refugee', 'strategic partnership', 'defence cooperation',
    ],
    tags: ['International Relations'], gs: 'GS2', use: 'Mains',
    reason: 'covers foreign policy, bilateral relations, and geopolitical dynamics.',
  },
  {
    keywords: [
      'terrorism', 'insurgency', 'border security', 'cybercrime', 'smuggling', 'police reform',
      'naxal', 'maoist', 'militant', 'terror', 'terrorist', 'bomb blast', 'explosion',
      'encounter', 'nia', 'crpf', 'bsf', 'drug trafficking', 'narcotics',
      'money laundering', 'hawala', 'fake currency', 'infiltration', 'separatist',
      'organized crime', 'arms smuggling',
    ],
    tags: ['Internal Security'], gs: 'GS3', use: 'Mains',
    reason: 'relates to law enforcement, national security, and internal threats.',
  },
  {
    keywords: [
      'space', 'satellite', 'semiconductor', 'biotechnology', 'research', 'digital',
      'isro', 'nasa', 'chandrayaan', 'gaganyaan', 'artificial intelligence',
      'machine learning', '5g', 'quantum', 'gene editing', 'crispr', 'genomics',
      'vaccine', 'nuclear', 'defence technology', 'electric vehicle', 'drone',
      'cybersecurity', 'cyber attack', 'data privacy', 'deepfake', 'innovation',
      'digital india', 'technology', 'patent', 'fintech',
    ],
    tags: ['Science and Technology'], gs: 'GS3', use: 'Prelims',
    reason: 'highlights technological advancement and scientific research relevant to GS3.',
  },
  {
    keywords: [
      'heritage', 'archaeological', 'artefact', 'artifact', 'museum', 'monument',
      'world heritage', 'unesco', 'excavation', 'ancient', 'medieval',
      'freedom fighter', 'freedom movement', 'independence movement', 'partition',
      'classical dance', 'classical music', 'folk art', 'traditional craft',
      'national monument', 'asi', 'civilization',
    ],
    tags: ['History & Culture'], gs: 'GS1', use: 'Prelims',
    reason: 'covers Indian history, cultural heritage, and art relevant to GS1.',
  },
];

function keywordMatch(keyword, text) {
  return new RegExp('\\b' + keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b').test(text);
}

function augmentData() {
  data.studyTopics = new Set();
  data.studyWorthyCount = 0;

  data.headlines.forEach(headline => {
    const titleLower = headline.title.toLowerCase();
    let matchedRule = rules.find(r => r.keywords.some(k => keywordMatch(k, titleLower)));

    if (matchedRule) {
      headline.studyPriority = (headline.priority === 'Lead' || headline.priority === 'High') ? 'High-yield' : 'Useful';
      headline.upscTags = matchedRule.tags;
      headline.gsPapers = matchedRule.gs.split(', ');
      headline.examUse = [matchedRule.use];
      headline.whyStudy = matchedRule.reason;

      matchedRule.tags.forEach(t => data.studyTopics.add(t));
      data.studyWorthyCount++;
    } else {
      headline.studyPriority = 'General update';
      headline.upscTags = [];
      headline.gsPapers = [];
      headline.examUse = [];
      headline.whyStudy = '';
    }

    // LLM enrichment overrides rule-based priority when available
    if (headline.enrichment?.upscRelevance) {
      const relevanceMap = { High: 'High-yield', Medium: 'Useful', Low: 'General update' };
      const mapped = relevanceMap[headline.enrichment.upscRelevance];
      if (mapped) headline.studyPriority = mapped;
    }
  });

  data.topicList = Array.from(data.studyTopics).sort();

  // Build cluster peer map: clusterId → non-lead headlines in that cluster
  data.clusterMap = {};
  data.headlines.forEach(h => {
    if (h.clusterId && !(h.isClusterLead ?? true)) {
      if (!data.clusterMap[h.clusterId]) data.clusterMap[h.clusterId] = [];
      data.clusterMap[h.clusterId].push(h);
    }
  });
}

// --- Mode ---
const TOPIC_EMOJI = {
  'Economy': '📈',
  'Environment': '🌿',
  'Polity': '🏛️',
  'Governance': '⚖️',
  'Science and Technology': '🔬',
  'International Relations': '🌐',
  'Society': '🤝',
  'Social Justice': '🤝',
  'Internal Security': '🛡️',
  'History & Culture': '🏺',
};

const MODE_LABELS = {
  upsc:     ['Headlines today', 'Must-Know for UPSC', 'Ongoing stories',  'Sources active'],
  informed: ['Headlines today', 'Essential reads',    'Running stories',  'Sources active'],
  explorer: ['Headlines today', 'Deep dives',         'Story threads',    'Sources active'],
};

let currentMode = localStorage.getItem('velugo-mode') || 'upsc';

function setMode(mode) {
  currentMode = mode;
  localStorage.setItem('velugo-mode', mode);
  document.body.classList.remove('mode-upsc', 'mode-informed', 'mode-explorer');
  document.body.classList.add(`mode-${mode}`);
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === mode);
  });
  renderHeaderAndSummary();
}

// --- State ---
let activeTopicFilter = 'All';

// --- Rendering ---
function renderHeaderAndSummary() {
  elements.timestamp.textContent = `Edition ${data.editionDate} · Updated ${formatDateTime(data.generatedAt)}`;
  
  const okCnt = data.sourceStatus.filter(s => s.status === 'ok').length;
  const errCnt = data.sourceStatus.length - okCnt;

  elements.statusBadge.textContent = errCnt > 0 ? 'Needs review' : 'Ready';
  if (errCnt > 0) {
    elements.statusBadge.classList.replace('ready', 'warn');
  }

  const ongoingCount = data.headlines.filter(h => (h.storyDayCount || 0) > 1).length;
  const modeLabels = MODE_LABELS[currentMode] || MODE_LABELS.upsc;
  const tiles = [
    { value: data.fetchStatus?.accepted ?? data.headlines.length, label: modeLabels[0], accent: false },
    { value: data.studyWorthyCount, label: modeLabels[1], accent: true },
    { value: ongoingCount, label: modeLabels[2], accent: false },
    { value: data.sources.length, label: errCnt > 0 ? `Sources (${errCnt} failed)` : modeLabels[3], accent: false, warn: errCnt > 0 },
  ];
  elements.dailyInsightSummary.innerHTML = tiles.map(t => `
    <div class="stat-tile${t.accent ? ' stat-tile--accent' : ''}${t.warn ? ' stat-tile--warn' : ''}">
      <span class="stat-value">${t.value}</span>
      <span class="stat-label">${t.label}</span>
    </div>
  `).join('');
}

function renderSourceHealth() {
  const okCnt = data.sourceStatus.filter(s => s.status === 'ok').length;
  const errCnt = data.sourceStatus.length - okCnt;

  elements.sourceHealthSummaryDisclosure.textContent = `Source health: ${okCnt} ok, ${errCnt} failed`;
  elements.sourceHealthList.replaceChildren();

  const sourceMap = new Map(data.sources.map(s => [s.id, s]));

  data.sourceStatus.forEach(status => {
    const src = sourceMap.get(status.sourceId) || {};
    const hasErr = status.status !== 'ok';

    const card = document.createElement('div');
    card.className = `source-card ${hasErr ? 'error' : ''}`;
    if (hasErr) card.style.borderColor = 'var(--warn-bg)';

    card.innerHTML = `
      <h3>${status.source} <span class="status-badge ${hasErr ? 'warn' : 'ready'}" style="float: right;">${hasErr ? 'Error' : 'OK'}</span></h3>
      <p class="source-meta-text">${titleCase(src.sourceType || status.sourceType)} · ${src.section || status.section} · ${status.accepted} accepted, ${status.skipped} skipped</p>
      <p class="source-meta-text" style="color: ${hasErr ? 'var(--warn)' : 'var(--muted)'}; font-size: 0.75rem;">${status.error || src.policyNotes || 'Public source feed.'}</p>
    `;
    elements.sourceHealthList.append(card);
  });
}

function createTagHTML(text, type) {
  let cls = 'tag priority-general';
  if (type === 'High-yield') cls = 'tag priority-high-yield';
  else if (type === 'Useful') cls = 'tag priority-useful';
  return `<span class="${cls}">${text}</span>`;
}

function renderFilters() {
  elements.topicChips.replaceChildren();

  const createChip = (label, displayLabel) => {
    const btn = document.createElement('button');
    btn.className = `chip ${activeTopicFilter === label ? 'active' : ''}`;
    btn.textContent = displayLabel || label;
    btn.onclick = () => {
      activeTopicFilter = label;
      renderFilters();
      renderGrids();
    };
    return btn;
  };

  elements.topicChips.append(createChip('All'));
  data.topicList.forEach(topic => {
    const emoji = TOPIC_EMOJI[topic];
    elements.topicChips.append(createChip(topic, emoji ? `${emoji} ${topic}` : topic));
  });
}

function renderGrids() {
  const q = elements.searchInput.value.toLowerCase().trim();

  // Filter fn
  const matchFilter = (h) => {
    const matchesTopic = activeTopicFilter === 'All' || h.upscTags.includes(activeTopicFilter);
    const matchesQ = !q || 
      h.title.toLowerCase().includes(q) || 
      h.source.toLowerCase().includes(q) || 
      h.upscTags.some(t => t.toLowerCase().includes(q)) || 
      h.gsPapers.some(g => g.toLowerCase().includes(q)) || 
      h.examUse.some(e => e.toLowerCase().includes(q));
    return matchesTopic && matchesQ;
  };

  // Only show cluster leads (unclustered headlines have isClusterLead=undefined, treated as true)
  const filtered = data.headlines.filter(h => (h.isClusterLead ?? true) && matchFilter(h));

  // Split into must-know and all
  const mustKnow = filtered.filter(h => h.studyPriority !== 'General update');
  if (elements.mustKnowCount) elements.mustKnowCount.textContent = mustKnow.length;
  if (elements.allHeadlinesCount) elements.allHeadlinesCount.textContent = filtered.length;

  const renderClusterLinks = (peers) => {
    if (!peers.length) return '';
    const unique = [...new Map(peers.map(p => [p.source, p])).values()].slice(0, 3);
    const more = peers.length - unique.length;
    const links = unique.map(p => `<a href="${p.url}" target="_blank" rel="noreferrer">${p.source}</a>`).join(', ');
    return `<div class="cluster-links">Also covered by: ${links}${more > 0 ? ` +${more} more` : ''}</div>`;
  };

  elements.mustKnowGrid.replaceChildren();
  if (mustKnow.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = (activeTopicFilter !== 'All' || q) ? `No must-know headlines match your filters.` : `No high-yield study items found yet. You can still scan all collected headlines below.`;
    elements.mustKnowGrid.append(empty);
  } else {
    mustKnow.forEach(h => {
      const card = document.createElement('article');
      card.className = 'card must-know-card';
      card.dataset.priority = h.studyPriority;

      const mkPeers = h.clusterId ? (data.clusterMap[h.clusterId] || []) : [];
      card.innerHTML = `
        <div class="card-meta">
          ${createTagHTML(h.studyPriority, h.studyPriority)}
          <span>${h.gsPapers.join(', ')}</span> ·
          <span>${h.upscTags.join(' · ')}</span> ·
          <span>${h.examUse.join(', ')}</span>
          ${mkPeers.length > 0 ? `<span class="cluster-badge">${h.clusterSize} sources</span>` : ''}
        </div>
        ${h.enrichment?.topic ? `<div class="topic-path">${h.enrichment.topic}</div>` : ''}
        <h3 class="card-title"><a href="${h.url}" target="_blank" rel="noreferrer">${applyGlossary(h.title)}</a></h3>
        ${h.excerpt ? `<p class="card-excerpt">${applyGlossary(h.excerpt)}</p>` : ''}
        ${h.enrichment?.examAngle ? `<p class="exam-angle">${h.enrichment.examAngle}</p>` : ''}
        ${renderFacts(h.facts)}
        ${renderStoryThread(h)}
        <p class="why-matters"><b>Why it matters:</b> ${h.enrichment?.whyItMatters || h.whyStudy}</p>
        <div class="card-source">${h.source} · <a href="${h.url}" target="_blank" rel="noreferrer">Open source &rarr;</a></div>
        ${renderClusterLinks(mkPeers)}
      `;
      elements.mustKnowGrid.append(card);
    });
  }

  elements.headlineGrid.replaceChildren();
  if (filtered.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = `No headlines match this search/filter.`;
    elements.headlineGrid.append(empty);
  } else {
    filtered.forEach(h => {
      const card = document.createElement('article');
      card.className = 'card all-headline-card';

      const peers = h.clusterId ? (data.clusterMap[h.clusterId] || []) : [];
      card.innerHTML = `
        <div class="card-meta">
          ${h.upscTags.length ? h.upscTags.map(t => `<span class="tag">${t}</span>`).join('') : '<span class="tag">General</span>'}
          ${peers.length > 0 ? `<span class="cluster-badge">${h.clusterSize} sources</span>` : ''}
        </div>
        ${h.enrichment?.topic ? `<div class="topic-path">${h.enrichment.topic}</div>` : ''}
        <h3 class="card-title"><a href="${h.url}" target="_blank" rel="noreferrer">${applyGlossary(h.title)}</a></h3>
        ${h.excerpt ? `<p class="card-excerpt">${applyGlossary(h.excerpt)}</p>` : ''}
        ${renderFacts(h.facts)}
        ${renderStoryThread(h)}
        <div class="card-source">${h.source} · ${formatDateTime(h.publishedAt)}</div>
        ${renderClusterLinks(peers)}
      `;
      elements.headlineGrid.append(card);
    });
  }
}

// --- Archive Navigation ---
let editionList = [];

function formatEditionLabel(dateStr) {
  try {
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata'
    }).format(new Date(dateStr + 'T00:00:00+05:30'));
  } catch {
    return dateStr;
  }
}

function updateNavButtons() {
  const idx = editionList.indexOf(data.editionDate);
  elements.prevEditionBtn.disabled = idx >= editionList.length - 1;
  elements.nextEditionBtn.disabled = idx <= 0;
}

async function loadEdition(dateStr) {
  const isLatest = editionList.length > 0 && dateStr === editionList[0];
  try {
    let payload;
    if (isLatest && window.__INDIA_HEADLINES__?.editionDate === dateStr) {
      payload = window.__INDIA_HEADLINES__;
    } else {
      const resp = await fetch(`../assets/data/editions/${dateStr}.json`);
      if (!resp.ok) throw new Error('not found');
      payload = await resp.json();
    }
    data = payload;
  } catch {
    return; // silently keep current edition if fetch fails
  }

  history.pushState(null, '', dateStr === editionList[0] ? location.pathname : `?edition=${dateStr}`);
  elements.editionSelect.value = dateStr;
  updateNavButtons();
  activeTopicFilter = 'All';
  augmentData();
  renderHeaderAndSummary();
  renderSourceHealth();
  renderFilters();
  renderGrids();
}

async function initArchiveNav() {
  try {
    const resp = await fetch('../assets/data/editions/index.json');
    if (!resp.ok) return;
    const index = await resp.json();
    editionList = index.editions || [];
  } catch {
    return;
  }

  if (editionList.length === 0) return;

  // Populate the select
  elements.editionSelect.replaceChildren();
  editionList.forEach(dateStr => {
    const opt = document.createElement('option');
    opt.value = dateStr;
    opt.textContent = formatEditionLabel(dateStr);
    elements.editionSelect.append(opt);
  });

  // Set current selection
  const current = data?.editionDate || editionList[0];
  elements.editionSelect.value = current;
  updateNavButtons();

  // Wire up controls
  elements.editionSelect.addEventListener('change', () => loadEdition(elements.editionSelect.value));

  elements.prevEditionBtn.addEventListener('click', () => {
    const idx = editionList.indexOf(data.editionDate);
    if (idx < editionList.length - 1) loadEdition(editionList[idx + 1]);
  });

  elements.nextEditionBtn.addEventListener('click', () => {
    const idx = editionList.indexOf(data.editionDate);
    if (idx > 0) loadEdition(editionList[idx - 1]);
  });
}

// --- Initialization ---
elements.searchInput.addEventListener('input', renderGrids);

document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
});

(async () => {
  // Check if a specific edition is requested via URL param
  const params = new URLSearchParams(location.search);
  const requestedEdition = params.get('edition');
  if (requestedEdition && requestedEdition !== data?.editionDate) {
    try {
      const resp = await fetch(`../assets/data/editions/${requestedEdition}.json`);
      if (resp.ok) data = await resp.json();
    } catch { /* fall through to default */ }
  }

  await loadGlossary();
  setMode(currentMode);

  augmentData();
  renderHeaderAndSummary();
  renderSourceHealth();
  renderFilters();
  renderGrids();

  // Init archive nav after first render (non-blocking)
  initArchiveNav();
})();
