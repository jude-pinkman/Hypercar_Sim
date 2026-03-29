/**
 * f1-race-calendar.js — 2026 Season Calendar
 * OFFLINE-FIRST: calendar data embedded, no backend required.
 */

// ─── Embedded 2026 calendar ───────────────────────────────────────────────────
const CALENDAR_2026 = [
  {
    "round": 1,
    "name": "Australian Grand Prix",
    "circuit": "AUS",
    "date": "2026-03-15",
    "status": "completed"
  },
  {
    "round": 2,
    "name": "Chinese Grand Prix",
    "circuit": "CHN",
    "date": "2026-03-22",
    "status": "upcoming"
  },
  {
    "round": 3,
    "name": "Japanese Grand Prix",
    "circuit": "JPN",
    "date": "2026-04-05",
    "status": "upcoming"
  },
  {
    "round": 4,
    "name": "Miami Grand Prix",
    "circuit": "MIA",
    "date": "2026-05-03",
    "status": "upcoming"
  },
  {
    "round": 5,
    "name": "Grand Prix de Monaco",
    "circuit": "MON",
    "date": "2026-05-24",
    "status": "upcoming"
  },
  {
    "round": 6,
    "name": "Canadian Grand Prix",
    "circuit": "CAN",
    "date": "2026-06-14",
    "status": "upcoming"
  },
  {
    "round": 7,
    "name": "Gran Premio de Barcelona-Catalunya",
    "circuit": "BAR",
    "date": "2026-06-28",
    "status": "upcoming"
  },
  {
    "round": 8,
    "name": "Austrian Grand Prix",
    "circuit": "AUT",
    "date": "2026-07-05",
    "status": "upcoming"
  },
  {
    "round": 9,
    "name": "British Grand Prix",
    "circuit": "GBR",
    "date": "2026-07-19",
    "status": "upcoming"
  },
  {
    "round": 10,
    "name": "Belgian Grand Prix",
    "circuit": "BEL",
    "date": "2026-07-26",
    "status": "upcoming"
  },
  {
    "round": 11,
    "name": "Hungarian Grand Prix",
    "circuit": "HUN",
    "date": "2026-08-02",
    "status": "upcoming"
  },
  {
    "round": 12,
    "name": "Dutch Grand Prix",
    "circuit": "NED",
    "date": "2026-08-30",
    "status": "upcoming"
  },
  {
    "round": 13,
    "name": "Gran Premio d'Italia",
    "circuit": "ITA",
    "date": "2026-09-06",
    "status": "upcoming"
  },
  {
    "round": 14,
    "name": "Azerbaijan Grand Prix",
    "circuit": "AZE",
    "date": "2026-09-20",
    "status": "upcoming"
  },
  {
    "round": 15,
    "name": "Singapore Grand Prix",
    "circuit": "SIN",
    "date": "2026-10-04",
    "status": "upcoming"
  },
  {
    "round": 16,
    "name": "United States Grand Prix",
    "circuit": "USA",
    "date": "2026-10-18",
    "status": "upcoming"
  },
  {
    "round": 17,
    "name": "Gran Premio de la Ciudad de M\u00e9xico",
    "circuit": "MEX",
    "date": "2026-10-25",
    "status": "upcoming"
  },
  {
    "round": 18,
    "name": "Grande Pr\u00eamio de S\u00e3o Paulo",
    "circuit": "BRA",
    "date": "2026-11-08",
    "status": "upcoming"
  },
  {
    "round": 19,
    "name": "Las Vegas Grand Prix",
    "circuit": "LVG",
    "date": "2026-11-21",
    "status": "upcoming"
  },
  {
    "round": 20,
    "name": "Qatar Airways Qatar Grand Prix",
    "circuit": "QAT",
    "date": "2026-11-29",
    "status": "upcoming"
  },
  {
    "round": 21,
    "name": "Abu Dhabi Grand Prix",
    "circuit": "ABU",
    "date": "2026-12-06",
    "status": "upcoming"
  }
];

const CIRCUIT_FLAGS = {"AUS": "\ud83c\udde6\ud83c\uddfa", "CHN": "\ud83c\udde8\ud83c\uddf3", "JPN": "\ud83c\uddef\ud83c\uddf5", "USA": "\ud83c\uddfa\ud83c\uddf8", "MCO": "\ud83c\uddf2\ud83c\udde8", "CAN": "\ud83c\udde8\ud83c\udde6", "ESP": "\ud83c\uddea\ud83c\uddf8", "AUT": "\ud83c\udde6\ud83c\uddf9", "GBR": "\ud83c\uddec\ud83c\udde7", "BEL": "\ud83c\udde7\ud83c\uddea", "HUN": "\ud83c\udded\ud83c\uddfa", "NED": "\ud83c\uddf3\ud83c\uddf1", "ITA": "\ud83c\uddee\ud83c\uddf9", "AZE": "\ud83c\udde6\ud83c\uddff", "SGP": "\ud83c\uddf8\ud83c\uddec", "MEX": "\ud83c\uddf2\ud83c\uddfd", "BRA": "\ud83c\udde7\ud83c\uddf7", "QAT": "\ud83c\uddf6\ud83c\udde6", "UAE": "\ud83c\udde6\ud83c\uddea"};

class F1CalendarManager {
    constructor() {
        this.setupTabs();
        this.render();
    }

    setupTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.getAttribute('data-tab');
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(`tab-${tab}`)?.classList.add('active');
            });
        });
    }

    render() {
        const container = document.getElementById('calendar-content');
        if (!container) return;

        const today = new Date('2026-03-19');
        const races  = CALENDAR_2026;

        // Find current/next race index
        let nextIdx = races.findIndex(r => new Date(r.date) >= today);
        if (nextIdx === -1) nextIdx = races.length - 1;

        let html = `
          <div class="cal-header">
            <span class="cal-season">🏁 2026 SEASON</span>
            <span class="cal-progress">${nextIdx} / ${races.length} races</span>
          </div>
          <div class="cal-list">`;

        races.forEach((race, i) => {
            const raceDate  = new Date(race.date);
            const isPast    = race.status === 'completed';
            const isCurrent = (i === nextIdx);
            const dateStr   = raceDate.toLocaleDateString('en-GB', { day:'numeric', month:'short' });
            const flag      = CIRCUIT_FLAGS[race.circuit] || '🏁';

            let cls = 'cal-race';
            if (isPast)    cls += ' cal-done';
            if (isCurrent) cls += ' cal-next';

            html += `
              <div class="${cls}">
                <span class="cal-rnd">R${race.round}</span>
                <span class="cal-flag">${flag}</span>
                <span class="cal-name">${race.name}</span>
                <span class="cal-date">${dateStr}</span>
                <span class="cal-tick">${isPast ? '✓' : isCurrent ? '●' : '◯'}</span>
              </div>`;
        });

        html += '</div>';
        container.innerHTML = html;
    }
}

// Init when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { window.calendarManager = new F1CalendarManager(); });
} else {
    window.calendarManager = new F1CalendarManager();
}
