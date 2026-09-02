import test from 'node:test';
import assert from 'node:assert/strict';
import { collectItems, detectApiVersion, flattenLead, normalizeSourceUrl } from './flatten.js';

test('flattenLead maps Unipile payload to CSV columns', () => {
  const row = flattenLead({
    name: 'Jane Doe',
    headline: 'VP Sales',
    company: { name: 'Acme Inc' },
    location: 'Madrid, Spain',
    public_profile_url: 'https://www.linkedin.com/in/janedoe',
    id: 'sn-123',
    network_distance: '2nd',
  });

  assert.equal(row.full_name, 'Jane Doe');
  assert.equal(row.job_title, 'VP Sales');
  assert.equal(row.company_name, 'Acme Inc');
  assert.equal(row.linkedin_url, 'https://www.linkedin.com/in/janedoe');
  assert.equal(row.sales_nav_id, 'sn-123');
  assert.equal(row.connection_degree, '2nd');
});

test('normalizeSourceUrl accepts list URL or numeric id', () => {
  assert.equal(
    normalizeSourceUrl('123456789', 'list'),
    'https://www.linkedin.com/sales/lists/people/123456789',
  );
  assert.match(
    normalizeSourceUrl('https://www.linkedin.com/sales/lists/people/999', 'list'),
    /\/999$/,
  );
});

test('normalizeSourceUrl rejects invalid search URL', () => {
  assert.throws(() => normalizeSourceUrl('https://linkedin.com/in/foo', 'search'));
});

test('detectApiVersion identifies v2 default', () => {
  assert.equal(detectApiVersion('https://api.unipile.com/v2'), false);
  assert.equal(detectApiVersion('https://api.unipile.com/api/v1'), true);
});

test('collectItems finds nested arrays', () => {
  assert.equal(collectItems({ items: [{ id: 1 }] }).length, 1);
  assert.equal(collectItems({ leads: [{ id: 2 }] }).length, 1);
});
