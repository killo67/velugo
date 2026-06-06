let data = window.__INDIA_HEADLINES__;

// --- DOM Elements ---
const elements = {
  timestamp: document.getElementById("timestamp"),
  statusBadge: document.getElementById("statusBadge"),
  dailyInsightSummary: document.getElementById("dailyInsightSummary"),
  mustKnowGrid: document.getElementById("mustKnowGrid"),
  mustKnowCount: document.getElementById("mustKnowCount"),
  allHeadlinesCount: document.getElementById("allHeadlinesCount"),
  allHeadlinesSection: document.querySelector(".all-headlines-section"),
  headlineGrid: document.getElementById("headlineGrid"),
  topicChips: document.getElementById("topicChips"),
  searchInput: document.getElementById("searchInput"),
  sourceHealthSummaryDisclosure: document.getElementById("sourceHealthSummaryDisclosure"),
  sourceHealthList: document.getElementById("sourceHealthList"),
  editionSelect: document.getElementById("editionSelect"),
  prevEditionBtn: document.getElementById("prevEditionBtn"),
  nextEditionBtn: document.getElementById("nextEditionBtn"),
  storyMapBtn: document.getElementById("storyMapBtn"),
  storyMapSection: document.getElementById("storyMapSection"),
  storyMapCount: document.getElementById("storyMapCount"),
  storyMapDateAxis: document.getElementById("storyMapDateAxis"),
  storyMapRows: document.getElementById("storyMapRows"),
};

// --- Theme Toggle & View Transitions ---
const transitionView = (callback) => {
  if (document.startViewTransition) {
    document.startViewTransition(callback);
  } else {
    callback();
  }
};

function initTheme() {
  const toggleBtn = document.getElementById("themeToggleBtn");
  const storedTheme = localStorage.getItem("velugo-theme");
  
  const setTheme = (theme) => {
    if (theme === "dark") {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
    localStorage.setItem("velugo-theme", theme);
  };

  if (storedTheme) {
    setTheme(storedTheme);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    setTheme("dark");
  }

  toggleBtn?.addEventListener("click", () => {
    const isDark = document.body.classList.contains("dark");
    transitionView(() => {
      setTheme(isDark ? "light" : "dark");
    });
  });
}

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

const SOURCE_DOMAINS = {
  'The Hindu':          'thehindu.com',
  'The Indian Express': 'indianexpress.com',
  'Times of India':     'timesofindia.com',
  'NDTV':               'ndtv.com',
  'Hindustan Times':    'hindustantimes.com',
  'LiveMint':           'livemint.com',
  'Mint':               'livemint.com',
  'PIB':                'pib.gov.in',
  'DD News':            'ddnews.gov.in',
  'Business Standard':  'business-standard.com',
  'The Wire':           'thewire.in',
  'Scroll':             'scroll.in',
  'The Print':          'theprint.in',
  'News18':             'news18.com',
};

function faviconHTML(source) {
  const domain = SOURCE_DOMAINS[source];
  if (!domain) return '';
  return `<img class="source-favicon" src="https://www.google.com/s2/favicons?domain=${domain}&sz=16" alt="" loading="lazy" width="14" height="14">`;
}

const MODE_LABELS = {
  upsc:     ['Headlines today', 'Must-Know for UPSC', 'Ongoing stories',  'Sources active'],
  informed: ['Headlines today', 'Essential reads',    'Running stories',  'Sources active'],
  explorer: ['Headlines today', 'Deep dives',         'Story threads',    'Sources active'],
};

let currentMode = localStorage.getItem('velugo-mode') || 'upsc';

function setMode(mode) {
  currentMode = mode;
  localStorage.setItem('velugo-mode', mode);
  transitionView(() => {
    document.body.classList.remove('mode-upsc', 'mode-informed', 'mode-explorer');
    document.body.classList.add(`mode-${mode}`);
    document.querySelectorAll('.mode-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    renderHeaderAndSummary();
  });
}

// --- Lens Wars ---
// --- Story follow (localStorage) ---
function getFollowedStories() {
  try { return new Set(JSON.parse(localStorage.getItem('velugo-followed-stories') || '[]')); }
  catch (_) { return new Set(); }
}
function followStory(key) {
  const followed = getFollowedStories();
  followed.add(key);
  localStorage.setItem('velugo-followed-stories', JSON.stringify([...followed]));
}
function isFollowing(key) {
  return !!key && getFollowedStories().has(key);
}
function followKeyFor(h) {
  return h.storyId || h.id;
}

// --- Supabase config (written to config.js by start.sh at container boot) ---
const SUPABASE_URL = window.__VELUGO_CONFIG__?.supabaseUrl || '';
const SUPABASE_ANON_KEY = window.__VELUGO_CONFIG__?.supabaseAnonKey || '';

async function submitVote(headlineId, editionDate, lens) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/lens_votes`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({ headline_id: headlineId, edition_date: editionDate, lens }),
    });
  } catch (_) { /* silent — local vote already saved */ }
}

async function fetchCounts(headlineId) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
  try {
    const resp = await fetch(
      `${SUPABASE_URL}/rest/v1/rpc/get_lens_counts`,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ p_headline_id: headlineId }),
      }
    );
    if (!resp.ok) return null;
    return await resp.json(); // { a: 42, b: 58 }
  } catch (_) { return null; }
}

async function fetchAndDisplayCounts(el, headlineId) {
  const counts = await fetchCounts(headlineId);
  if (!counts) return;
  const total = (counts.a || 0) + (counts.b || 0);
  if (total === 0) return;

  const pctA = Math.round((counts.a / total) * 100);
  const pctB = 100 - pctA;

  const btnA = el.querySelector('.lens-btn[data-lens="a"]');
  const btnB = el.querySelector('.lens-btn[data-lens="b"]');
  const pctSpanA = btnA?.querySelector('.lens-pct');
  const pctSpanB = btnB?.querySelector('.lens-pct');
  if (pctSpanA) pctSpanA.textContent = `${pctA}%`;
  if (pctSpanB) pctSpanB.textContent = `${pctB}%`;

  const crowd   = el.querySelector('.lens-crowd');
  const fillA   = el.querySelector('.lens-crowd-fill-a');
  const fillB   = el.querySelector('.lens-crowd-fill-b');
  const labelA  = el.querySelector('.lens-crowd-label-a');
  const labelB  = el.querySelector('.lens-crowd-label-b');
  const caption = el.querySelector('.lens-crowd-caption');

  if (crowd) crowd.classList.remove('hidden');

  // Animate fills from both ends toward center (requestAnimationFrame ensures transition fires)
  requestAnimationFrame(() => {
    if (fillA)  fillA.style.width  = `${pctA}%`;
    if (fillB)  fillB.style.width  = `${pctB}%`;
    if (labelA) { labelA.style.width = `${pctA}%`; labelA.textContent = `${pctA}%`; }
    if (labelB) labelB.textContent = `${pctB}%`;
  });

  if (caption) caption.textContent = `${total.toLocaleString()} readers weighed in`;
}

// Topic-level fallback pairs — used when API enrichment is unavailable.
// Keys match upscTags[] values assigned by augmentData() keyword rules.
const FALLBACK_LENS = {
  'Economy':                 ['Opportunity', 'Risk'],
  'Polity':                  ['Progress',    'Problem'],
  'Governance':              ['Progress',    'Problem'],
  'International Relations': ['Win',         'Gamble'],
  'Environment':             ['Needed',      'Costly'],
  'Internal Security':       ['Safety',      'Overreach'],
  'Science & Technology':    ['Breakthrough','Concern'],
  'Society':                 ['Help',        'Harm'],
  'Social Justice':          ['Help',        'Harm'],
  'History & Culture':       ['Preserve',    'Resist'],
  'Disaster Management':     ['Prepared',    'Delayed'],
};

function renderLensWars(h) {
  const fallback = FALLBACK_LENS[h.upscTags?.[0]];
  const lensA = h.enrichment?.lensA || fallback?.[0];
  const lensB = h.enrichment?.lensB || fallback?.[1];
  if (!lensA || !lensB) return '';
  return `
    <div class="lens-wars">
      <button class="lens-wars-trigger" type="button">Your take?</button>
      <div class="lens-wars-panel hidden">
        <p class="lens-sentence">
          <button class="lens-btn" type="button" data-lens="a"><span class="lens-label">${escapeHtml(lensA)}</span><span class="lens-pct"></span></button>
          or
          <button class="lens-btn" type="button" data-lens="b"><span class="lens-label">${escapeHtml(lensB)}</span><span class="lens-pct"></span></button>?
        </p>
        <div class="lens-crowd hidden">
          <div class="lens-crowd-labels">
            <span class="lens-crowd-label-a"></span>
            <span class="lens-crowd-label-b"></span>
          </div>
          <div class="lens-crowd-bar">
            <div class="lens-crowd-fill-a"></div>
            <div class="lens-crowd-fill-b"></div>
          </div>
          <p class="lens-crowd-caption"></p>
        </div>
        <div class="lens-track-prompt hidden">
          <span class="lens-track-text">${h.storyId && (h.storyDayCount || 0) >= 2 ? `📌 This story is evolving` : `📌 Watch how this story unfolds`}</span>
          <button class="lens-track-btn" type="button">Follow it</button>
        </div>
      </div>
    </div>`;
}

function applyLensVote(el, choice) {
  el.querySelectorAll('.lens-btn').forEach(btn => {
    const isChosen = btn.dataset.lens === choice;
    btn.classList.toggle('lens-btn--chosen', isChosen);
    btn.classList.toggle('lens-btn--other', !isChosen);
    btn.disabled = true;
  });
}

function updateTrackPrompt(el, h) {
  const prompt = el.querySelector('.lens-track-prompt');
  if (!prompt) return;
  prompt.classList.remove('hidden');

  const btn = prompt.querySelector('.lens-track-btn');
  if (!btn) return;

  const key = followKeyFor(h);
  const already = isFollowing(key);
  if (already) {
    btn.textContent = '★ Following';
    btn.disabled = true;
    btn.classList.add('lens-track-btn--active');
    return;
  }

  btn.onclick = (e) => {
    e.stopPropagation();
    followStory(key);
    btn.textContent = '★ Following';
    btn.disabled = true;
    btn.classList.add('lens-track-btn--active');
    if (!elements.storyMapSection.classList.contains('hidden')) {
      renderStoryMap();
    }
  };
}

async function wireupLensWars(card, h) {
  const el = card.querySelector('.lens-wars');
  if (!el) return;

  const trigger = el.querySelector('.lens-wars-trigger');
  const panel = el.querySelector('.lens-wars-panel');
  const editionDate = data.editionDate;

  const stored = localStorage.getItem(`velugo-lens-${h.id}`);
  if (stored) {
    panel.classList.remove('hidden');
    trigger.classList.add('hidden');
    applyLensVote(el, stored);
    fetchAndDisplayCounts(el, h.id);
    updateTrackPrompt(el, h);
  }

  trigger?.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.remove('hidden');
    trigger.classList.add('hidden');
  });

  el.querySelectorAll('.lens-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const choice = btn.dataset.lens;
      localStorage.setItem(`velugo-lens-${h.id}`, choice);
      applyLensVote(el, choice);
      updateTrackPrompt(el, h);
      await submitVote(h.id, editionDate, choice);
      fetchAndDisplayCounts(el, h.id);
    });
  });
}

// --- Story Map ---
let storyMapRendered = false;

const STORY_PHASE_CONFIG = {
  escalating: { label: '↑ Escalating', cls: 'escalating' },
  developing:  { label: '⟳ Developing',  cls: 'developing'  },
  resolving:   { label: '↓ Resolving',   cls: 'resolving'   },
  resolved:    { label: '✓ Resolved',    cls: 'resolved'    },
};

function renderStoryMap() {
  const fmtDate = d => new Intl.DateTimeFormat('en-IN', {
    day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata'
  }).format(new Date(d + 'T00:00:00+05:30'));

  // Deduplicate threaded stories by storyId, keep highest dayCount.
  // Also build a reverse map: every headline id that belongs to each storyId,
  // so a follow stored by h.id (before storyId was assigned) is still detected.
  const storyMap = new Map();
  const storyMemberIds = new Map(); // storyId → Set of headline ids in that story
  data.headlines.forEach(h => {
    if (!h.storyId || (h.storyDayCount || 0) < 2) return;
    const ex = storyMap.get(h.storyId);
    if (!ex || h.storyDayCount > ex.storyDayCount) storyMap.set(h.storyId, h);
    if (!storyMemberIds.has(h.storyId)) storyMemberIds.set(h.storyId, new Set());
    storyMemberIds.get(h.storyId).add(h.id);
  });

  const followedSet = getFollowedStories();
  const isStoryFollowed = (h) => {
    if (followedSet.has(h.storyId) || followedSet.has(h.id)) return true;
    const members = storyMemberIds.get(h.storyId);
    return members ? [...members].some(id => followedSet.has(id)) : false;
  };

  const stories = [...storyMap.values()].sort((a, b) => {
    const af = isStoryFollowed(a) ? 1 : 0;
    const bf = isStoryFollowed(b) ? 1 : 0;
    if (bf !== af) return bf - af;
    return (b.storyDayCount || 0) - (a.storyDayCount || 0);
  });

  if (elements.storyMapCount) elements.storyMapCount.textContent = stories.length;

  if (stories.length === 0) {
    elements.storyMapRows.innerHTML = '<p class="empty-state">No story threads yet — threads build as the same story appears across multiple days.</p>';
    elements.storyMapDateAxis.innerHTML = '';
    return;
  }

  // Collect + sort all dates across all stories
  const today = data.editionDate;
  const allDates = new Set([today]);
  stories.forEach(h => (h.storyEditions || []).forEach(e => allDates.add(e.date)));
  const sortedDates = [...allDates].sort();

  // Position helper: % along the timeline
  const minTime = new Date(sortedDates[0]).getTime();
  const maxTime = new Date(today).getTime();
  const range = maxTime - minTime || 1;
  const pct = d => Math.round((new Date(d).getTime() - minTime) / range * 100);

  // Date axis
  elements.storyMapDateAxis.innerHTML = sortedDates.map(d => `
    <span class="sm-axis-label ${d === today ? 'sm-axis-today' : ''}" style="left:${pct(d)}%">
      ${d === today ? 'Today' : fmtDate(d)}
    </span>
  `).join('');

  // Story rows
  elements.storyMapRows.innerHTML = stories.map(h => {
    const topic = (h.upscTags || [])[0] || 'General';
    const emoji = TOPIC_EMOJI[topic] || '📰';
    const editions = h.storyEditions || [];
    const shortTitle = h.title.length > 58 ? h.title.slice(0, 58) + '…' : h.title;

    const pastDots = editions.map(e => `
      <div class="sm-dot" style="left:${pct(e.date)}%" title="${fmtDate(e.date)}: ${escapeHtml(e.title)}">
        <a href="${e.url}" target="_blank" rel="noreferrer" class="sm-dot-link" aria-label="${fmtDate(e.date)}"></a>
      </div>`).join('');

    const todayDot = `<div class="sm-dot sm-dot--today" style="left:${pct(today)}%" title="Today: ${escapeHtml(h.title)}">
      <a href="${h.url}" target="_blank" rel="noreferrer" class="sm-dot-link" aria-label="Today"></a>
    </div>`;

    const phase = h.enrichment?.storyPhase;
    const phaseConf = STORY_PHASE_CONFIG[phase];
    const phaseBadge = phaseConf
      ? `<span class="sm-phase-badge sm-phase-badge--${phaseConf.cls}">${phaseConf.label}</span>`
      : '';
    const storyUpdate = h.enrichment?.storyUpdate;
    const followed = isStoryFollowed(h);
    const isResolved = phase === 'resolved';
    const followBadge = followed
      ? `<span class="sm-following-badge">${isResolved ? '✓ Story resolved' : '★ Following'}</span>`
      : '';
    const rowCls = followed ? (isResolved ? 'sm-row sm-row--resolved' : 'sm-row sm-row--following') : 'sm-row';

    return `
      <div class="${rowCls}">
        <div class="sm-row-label">
          <span class="sm-topic">${emoji} ${topic}</span>
          <a href="${h.url}" target="_blank" rel="noreferrer" class="sm-title">${escapeHtml(shortTitle)}</a>
          ${storyUpdate ? `<span class="sm-story-update">${escapeHtml(storyUpdate)}</span>` : ''}
          <div class="sm-badges-row">
            <span class="sm-day-badge">Day ${h.storyDayCount}</span>
            ${phaseBadge}
            ${followBadge}
          </div>
        </div>
        <div class="sm-track">${pastDots}${todayDot}</div>
      </div>`;
  }).join('');
}

function toggleStoryMap() {
  const isOpen = !elements.storyMapSection.classList.contains('hidden');
  if (isOpen) {
    elements.storyMapSection.classList.add('hidden');
    elements.storyMapBtn.classList.remove('active');
  } else {
    elements.storyMapSection.classList.remove('hidden');
    elements.storyMapBtn.classList.add('active');
    if (!storyMapRendered) {
      renderStoryMap();
      storyMapRendered = true;
    }
  }
}

// --- State ---
let activeTopicFilter = 'All';
let mkLimit  = 9;   // Must-Know cards shown initially
let allLimit = 12;  // All-Headlines cards shown initially

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
    { value: data.fetchStatus?.accepted ?? data.headlines.length, label: modeLabels[0], accent: false, stat: 'total' },
    { value: data.studyWorthyCount, label: modeLabels[1], accent: true, stat: 'mustknow' },
    { value: ongoingCount, label: modeLabels[2], accent: false, stat: 'ongoing' },
    { value: data.sources.length, label: errCnt > 0 ? `Sources (${errCnt} failed)` : modeLabels[3], accent: false, warn: errCnt > 0, stat: 'sources' },
  ];
  elements.dailyInsightSummary.innerHTML = tiles.map(t => `
    <div class="stat-tile${t.accent ? ' stat-tile--accent' : ''}${t.warn ? ' stat-tile--warn' : ''}" data-stat="${t.stat}">
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
      mkLimit  = 9;
      allLimit = 12;
      transitionView(() => {
        renderFilters();
        renderGrids();
      });
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

  // Split into must-know and general (no duplicates in All Headlines)
  const mustKnow      = filtered.filter(h => h.studyPriority !== 'General update');
  const generalOnly   = filtered.filter(h => h.studyPriority === 'General update');
  if (elements.mustKnowCount) elements.mustKnowCount.textContent = mustKnow.length;
  if (elements.allHeadlinesCount) elements.allHeadlinesCount.textContent = generalOnly.length;

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
    mustKnow.slice(0, mkLimit).forEach((h, idx) => {
      const card = document.createElement('article');
      card.className = 'card must-know-card';
      card.dataset.priority = h.studyPriority;
      if (h.upscTags?.[0]) card.dataset.topic = h.upscTags[0];

      // Unique view-transition-name for animation matching
      const vtName = 'card_' + h.id.replace(/[^a-zA-Z0-9_-]/g, '_');
      card.style.viewTransitionName = 'mk_' + vtName;

      // Handle card click to open detail dialog (ignoring links/details/lens-wars clicks)
      card.addEventListener('click', (e) => {
        if (e.target.closest('a') || e.target.closest('details') || e.target.closest('summary') || e.target.closest('.lens-wars')) {
          return;
        }
        e.preventDefault();
        openArticleModal(h);
      });

      const mkPeers = h.clusterId ? (data.clusterMap[h.clusterId] || []) : [];

      if (idx === 0) {
        // ── Hero card: full-width two-column layout ──────────────────────────
        card.classList.add('must-know-card--hero');
        card.innerHTML = `
          <div class="hero-col-left">
            <div class="hero-lead-badge">★ Today's Lead</div>
            <div class="card-meta">
              ${createTagHTML(h.studyPriority, h.studyPriority)}
              <span>${h.gsPapers.join(', ')}</span> ·
              <span>${h.upscTags.join(' · ')}</span>
              ${mkPeers.length > 0 ? `<span class="cluster-badge">${h.clusterSize} sources</span>` : ''}
              ${h.storyId && h.storyDayCount > 1 ? `<span class="thread-indicator" title="Running ${h.storyDayCount} days">↺ Day ${h.storyDayCount}</span>` : ''}
            </div>
            ${h.enrichment?.topic ? `<div class="topic-path">${h.enrichment.topic}</div>` : ''}
            <h3 class="card-title"><a href="${h.url}" target="_blank" rel="noreferrer">${applyGlossary(h.title)}</a></h3>
            ${h.excerpt ? `<p class="card-excerpt">${applyGlossary(h.excerpt)}</p>` : ''}
            <div class="card-source">${faviconHTML(h.source)}${h.source} · <a href="${h.url}" target="_blank" rel="noreferrer">Open source &rarr;</a></div>
            ${renderClusterLinks(mkPeers)}
          </div>
          <div class="hero-col-right">
            ${h.enrichment?.examAngle ? `<p class="exam-angle">${h.enrichment.examAngle}</p>` : ''}
            ${renderFacts(h.facts)}
            ${renderStoryThread(h)}
            <p class="why-matters"><b>Why it matters:</b> ${h.enrichment?.whyItMatters || h.whyStudy}</p>
            ${renderLensWars(h)}
          </div>
        `;
      } else {
        // ── Regular card ─────────────────────────────────────────────────────
        card.innerHTML = `
          <div class="card-meta">
            ${createTagHTML(h.studyPriority, h.studyPriority)}
            <span>${h.gsPapers.join(', ')}</span> ·
            <span>${h.upscTags.join(' · ')}</span> ·
            <span>${h.examUse.join(', ')}</span>
            ${mkPeers.length > 0 ? `<span class="cluster-badge">${h.clusterSize} sources</span>` : ''}
            ${h.storyId && h.storyDayCount > 1 ? `<span class="thread-indicator" title="This story has been running for ${h.storyDayCount} days">↺ Day ${h.storyDayCount}</span>` : ''}
          </div>
          ${h.enrichment?.topic ? `<div class="topic-path">${h.enrichment.topic}</div>` : ''}
          <h3 class="card-title"><a href="${h.url}" target="_blank" rel="noreferrer">${applyGlossary(h.title)}</a></h3>
          ${h.excerpt ? `<p class="card-excerpt">${applyGlossary(h.excerpt)}</p>` : ''}
          ${h.enrichment?.examAngle ? `<p class="exam-angle">${h.enrichment.examAngle}</p>` : ''}
          ${renderFacts(h.facts)}
          ${renderStoryThread(h)}
          <p class="why-matters"><b>Why it matters:</b> ${h.enrichment?.whyItMatters || h.whyStudy}</p>
          <div class="card-source">${faviconHTML(h.source)}${h.source} · <a href="${h.url}" target="_blank" rel="noreferrer">Open source &rarr;</a></div>
          ${renderClusterLinks(mkPeers)}
          ${renderLensWars(h)}
        `;
      }

      wireupLensWars(card, h);
      elements.mustKnowGrid.append(card);
    });

    // Show-more button for Must-Know
    if (mustKnow.length > mkLimit) {
      const remaining = mustKnow.length - mkLimit;
      const btn = document.createElement('button');
      btn.className = 'show-more-btn';
      btn.textContent = `Show ${remaining} more must-know articles`;
      btn.addEventListener('click', () => {
        mkLimit += 9;
        renderGrids();
      });
      elements.mustKnowGrid.append(btn);
    }
  }

  elements.headlineGrid.replaceChildren();
  const allVisible = generalOnly.slice(0, allLimit);

  // Hide the whole section when there are no general-only articles
  if (elements.allHeadlinesSection) {
    elements.allHeadlinesSection.style.display = generalOnly.length === 0 ? 'none' : '';
  }

  if (allVisible.length > 0) {
    allVisible.forEach(h => {
      const card = document.createElement('article');
      card.className = 'card all-headline-card';
      if (h.upscTags?.[0]) card.dataset.topic = h.upscTags[0];

      // Unique view-transition-name for animation matching
      const vtName = 'card_' + h.id.replace(/[^a-zA-Z0-9_-]/g, '_');
      card.style.viewTransitionName = 'all_' + vtName;

      // Handle card click to open detail dialog (ignoring links/details element clicks)
      card.addEventListener('click', (e) => {
        if (e.target.closest('a') || e.target.closest('details') || e.target.closest('summary')) {
          return;
        }
        e.preventDefault();
        openArticleModal(h);
      });

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
        <div class="card-source">${faviconHTML(h.source)}${h.source} · ${formatDateTime(h.publishedAt)}</div>
        ${renderClusterLinks(peers)}
      `;
      elements.headlineGrid.append(card);
    });

    // Show-more button for All Headlines
    if (generalOnly.length > allLimit) {
      const remaining = generalOnly.length - allLimit;
      const btn = document.createElement('button');
      btn.className = 'show-more-btn';
      btn.textContent = `Show ${remaining} more headlines`;
      btn.addEventListener('click', () => {
        allLimit += 12;
        renderGrids();
      });
      elements.headlineGrid.append(btn);
    }
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
  mkLimit  = 9;
  allLimit = 12;
  storyMapRendered = false;

  transitionView(() => {
    augmentData();
    renderHeaderAndSummary();
    renderSourceHealth();
    renderFilters();
    renderGrids();
    // Re-render story map if it's open
    if (!elements.storyMapSection.classList.contains('hidden')) {
      renderStoryMap();
      storyMapRendered = true;
    }
  });
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
elements.searchInput.addEventListener('input', () => {
  mkLimit  = 9;
  allLimit = 12;
  transitionView(() => renderGrids());
});

document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => setMode(btn.dataset.mode));
});

elements.storyMapBtn?.addEventListener('click', toggleStoryMap);

// --- Article Detail Modal Logic ---
let lastFocusedElement = null;

function openArticleModal(headline) {
  const modal = document.getElementById("articleModal");
  if (!modal) return;

  lastFocusedElement = document.activeElement;

  const topicPath = document.getElementById("modalTopicPath");
  topicPath.textContent = headline.enrichment?.topic || headline.upscTags?.join(' · ') || 'General Update';
  
  const source = document.getElementById("modalSource");
  source.textContent = headline.source;
  
  const date = document.getElementById("modalDate");
  date.textContent = formatDateTime(headline.publishedAt);
  
  const title = document.getElementById("modalTitle");
  title.innerHTML = applyGlossary(headline.title);

  const badges = document.getElementById("modalBadges");
  badges.replaceChildren();
  if (headline.studyPriority && headline.studyPriority !== 'General update') {
    badges.innerHTML += createTagHTML(headline.studyPriority, headline.studyPriority);
  }
  if (headline.gsPapers && headline.gsPapers.length) {
    const gsSpan = document.createElement('span');
    gsSpan.className = 'tag';
    gsSpan.textContent = headline.gsPapers.join(', ');
    badges.appendChild(gsSpan);
  }
  if (headline.upscTags && headline.upscTags.length) {
    headline.upscTags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tag;
      badges.appendChild(tagSpan);
    });
  }

  const excerpt = document.getElementById("modalExcerpt");
  const contentText = headline.articleText || headline.excerpt || '';
  excerpt.innerHTML = contentText ? applyGlossary(contentText) : 'No description available.';

  const examAngleContainer = document.getElementById("modalExamAngleContainer");
  const examAngle = document.getElementById("modalExamAngle");
  const examAngleText = headline.enrichment?.examAngle || headline.examUse?.join(', ');
  if (examAngleText) {
    examAngle.textContent = examAngleText;
    examAngleContainer.classList.remove("hidden");
  } else {
    examAngleContainer.classList.add("hidden");
  }

  const whyStudyContainer = document.getElementById("modalWhyStudyContainer");
  const whyStudy = document.getElementById("modalWhyStudy");
  const whyStudyText = headline.enrichment?.whyItMatters || headline.whyStudy;
  if (whyStudyText) {
    whyStudy.textContent = whyStudyText;
    whyStudyContainer.classList.remove("hidden");
  } else {
    whyStudyContainer.classList.add("hidden");
  }

  const factsContainer = document.getElementById("modalFactsContainer");
  const factsList = document.getElementById("modalFacts");
  if (headline.facts && headline.facts.length) {
    factsList.innerHTML = headline.facts
      .map(f => `<span class="fact-chip fact-chip--${f.type}" title="${f.type}">${f.text}</span>`)
      .join('');
    factsContainer.classList.remove("hidden");
  } else {
    factsContainer.classList.add("hidden");
  }

  const storyContainer = document.getElementById("modalStoryThreadContainer");
  const storyThread = document.getElementById("modalStoryThread");
  if (headline.storyDayCount && headline.storyDayCount >= 2 && headline.storyEditions) {
    const links = headline.storyEditions.map(e => {
      const label = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', timeZone: 'Asia/Kolkata' }).format(new Date(e.date));
      return `<li><a href="${e.url}" target="_blank" rel="noreferrer">${label} — ${escapeHtml(e.title)}</a></li>`;
    }).join('');
    storyThread.innerHTML = `<ul class="story-thread-panel" style="border-left-width: 3px; padding-left: 12px; margin: 0;">${links}</ul>`;
    storyContainer.classList.remove("hidden");
  } else {
    storyContainer.classList.add("hidden");
  }

  const sourceLink = document.getElementById("modalSourceLink");
  sourceLink.href = headline.url;

  modal.showModal();
  title.focus();
}

function closeArticleModal() {
  const modal = document.getElementById("articleModal");
  if (!modal) return;
  modal.close();
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
}

function initModalEvents() {
  const modal = document.getElementById("articleModal");
  const closeBtn = document.getElementById("closeModalBtn");
  const footerCloseBtn = document.getElementById("modalCloseBtn");

  closeBtn?.addEventListener("click", closeArticleModal);
  footerCloseBtn?.addEventListener("click", closeArticleModal);

  modal?.addEventListener("click", (e) => {
    const rect = modal.getBoundingClientRect();
    const isInDialog = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
    if (!isInDialog) {
      closeArticleModal();
    }
  });
}

(async () => {
  const params = new URLSearchParams(location.search);
  const requestedEdition = params.get('edition');
  if (requestedEdition && requestedEdition !== data?.editionDate) {
    try {
      const resp = await fetch(`../assets/data/editions/${requestedEdition}.json`);
      if (resp.ok) data = await resp.json();
    } catch { /* fall through to default */ }
  }

  await loadGlossary();
  initTheme();
  initModalEvents();
  setMode(currentMode);

  augmentData();
  renderHeaderAndSummary();
  renderSourceHealth();
  renderFilters();
  renderGrids();

  initArchiveNav();
})();
