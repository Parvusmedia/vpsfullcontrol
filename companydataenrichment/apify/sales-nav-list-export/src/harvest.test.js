import test from 'node:test';
import assert from 'node:assert/strict';
import {
  companyIndustry,
  companySize,
  domainFromWebsite,
  inferSeniority,
  joinSkills,
  mapEnrichedFields,
  parseTenureYears,
} from './harvest.js';

test('domainFromWebsite extracts host', () => {
  assert.equal(domainFromWebsite('https://www.acme.com/about'), 'acme.com');
  assert.equal(domainFromWebsite('acme.io'), 'acme.io');
});

test('parseTenureYears reads year tokens', () => {
  assert.equal(parseTenureYears('3 yrs 2 mos'), '3');
  assert.equal(parseTenureYears('1 year'), '1');
  assert.equal(parseTenureYears('8 mos'), '');
});

test('inferSeniority maps common titles', () => {
  assert.equal(inferSeniority('VP Sales EMEA'), 'VP');
  assert.equal(inferSeniority('Co-Founder'), 'Founder');
});

test('joinSkills joins unique skill names', () => {
  assert.equal(
    joinSkills({ skills: [{ name: 'Sales' }, { name: 'CRM' }, { name: 'Sales' }] }),
    'Sales; CRM',
  );
});

test('mapEnrichedFields builds enriched CSV columns', () => {
  const profile = {
    about: 'B2B leader',
    headline: 'VP Sales',
    skills: [{ name: 'Negotiation' }],
    languages: [{ name: 'English', proficiency: 'Native' }],
    experience: [{
      position: 'VP Sales',
      duration: '4 yrs',
      companyLinkedinUrl: 'https://www.linkedin.com/company/acme',
    }],
  };
  const company = {
    website: 'https://www.acme.com',
    industries: [{ name: 'Software' }],
    employeeCountRange: { start: 51, end: 200 },
    locations: [{ headquarter: true, parsed: { text: 'Madrid, Spain' } }],
  };
  const fields = mapEnrichedFields(profile, company, profile.experience[0]);
  assert.equal(fields.company_domain, 'acme.com');
  assert.equal(fields.company_industry, 'Software');
  assert.equal(fields.company_size, '51-200');
  assert.equal(fields.company_hq, 'Madrid, Spain');
  assert.equal(fields.seniority, 'VP');
  assert.equal(fields.tenure_years, '4');
  assert.equal(fields.profile_summary, 'B2B leader');
  assert.equal(fields.skills, 'Negotiation');
  assert.match(fields.languages, /English/);
});

test('companySize handles employeeCount fallback', () => {
  assert.equal(companySize({ employeeCount: 120 }), '120');
});

test('companyIndustry joins multiple industries', () => {
  assert.equal(
    companyIndustry({ industries: [{ name: 'SaaS' }, { title: 'IT Services' }] }),
    'SaaS; IT Services',
  );
});
