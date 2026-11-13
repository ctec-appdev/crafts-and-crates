/* Classify calendar dates in the venue's time zone, through the event day. */
(() => {
  const list = document.getElementById('event-list');
  const upcoming = document.getElementById('upcoming-events');
  const heading = document.getElementById('event-list-heading');
  if (!list || !upcoming || !heading) return;

  const months = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(new Date());
  const today = parts.find(p => p.type === 'year').value + '-' +
    parts.find(p => p.type === 'month').value + '-' + parts.find(p => p.type === 'day').value;
  let unknown = false;
  const future = [];
  list.querySelectorAll('.event-card').forEach(card => {
    const date = card.querySelector('.event-card-date');
    const match = date && date.textContent.trim().match(/^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})$/);
    if (!match) { unknown = true; return; }
    const month = months.indexOf(match[1]) + 1;
    const day = Number(match[2]);
    const year = Number(match[3]);
    const check = new Date(Date.UTC(year, month - 1, day));
    if (!month || check.getUTCFullYear() !== year || check.getUTCMonth() !== month - 1 || check.getUTCDate() !== day) {
      unknown = true;
      return;
    }
    const iso = `${match[3]}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    if (iso >= today) future.push({ card, iso });
  });
  future.sort((a, b) => a.iso.localeCompare(b.iso));
  const grid = upcoming.querySelector('.cards-grid');
  future.forEach(({ card }) => grid.appendChild(card));
  upcoming.hidden = future.length === 0;
  heading.textContent = unknown ? 'Other Events' : 'Previous Events';
})();
