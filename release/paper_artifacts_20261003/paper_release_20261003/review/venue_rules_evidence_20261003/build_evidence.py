from pathlib import Path
import shutil, hashlib, json, re, datetime, os, sys
try:
    import requests
except Exception:
    requests = None
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

ROOT = Path.cwd()
EV = ROOT / 'work' / 'paper' / 'review' / 'venue_rules_evidence_20261003'
RAW = EV / 'raw'
EXT = EV / 'extracts'
RAW.mkdir(parents=True, exist_ok=True); EXT.mkdir(parents=True, exist_ok=True)

# Existing source captures made during the venue audit. The destination names are stable
# and avoid changing any pre-existing project artifact.
copy_map = {
    'tim_authors.html':'tim_authors.html',
    'tim_templates.html':'tim_templates.html',
    'tim_charge.pdf':'tim_charge.pdf',
    'tim.html':'tim_landing.html',
    'trel_rs.html':'trel_rs.html',
    'trel_review_policy.pdf':'trel_review_policy.pdf',
    'trel_policy.txt':'trel_review_policy_extracted.txt',
    'trel_xplore.html':'trel_xplore_response.html',
    'taes_page.html':'taes_page.html',
    'taes_authors.html':'taes_authors.html',
    'taes_template.zip':'taes_template.zip',
    'ieee_src_0.html':'ieee_general_peer_review.html',
    'cas_cas.html':'cas_home.html',
    'clarivate_jcr_home.html':'clarivate_jcr_home.html',
    'jcr_main.js':'clarivate_jcr_bundle.js',
}
records = []
def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def observed_time(p):
    # Existing source files were written by the capture scripts in local Asia/Shanghai time.
    return datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
for src,dst in copy_map.items():
    p=ROOT/src
    if not p.exists():
        continue
    q=RAW/dst
    shutil.copy2(p,q)
    records.append({'artifact':str(q.relative_to(EV).as_posix()),'source_file':src,'capture_time_local':observed_time(p),'sha256':sha256(q),'bytes':q.stat().st_size})

# Fetch the exact accessibility guidance URL used in the handoff, saving it inside the permitted evidence directory.
if requests:
    u='https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/ieee-guidelines-on-advertising-accessibility-data-privacy/'
    try:
        r=requests.get(u,headers={'User-Agent':'Mozilla/5.0 BRPHM-audit/2026-10-03'},timeout=30)
        q=RAW/'ieee_accessibility_guidance.html'; q.write_bytes(r.content)
        records.append({'artifact':str(q.relative_to(EV).as_posix()),'url':u,'http_status':r.status_code,'final_url':str(r.url),'access_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':sha256(q),'bytes':len(r.content),'content_type':r.headers.get('content-type')})
    except Exception as e:
        (EV/'ieee_accessibility_fetch_error.txt').write_text(repr(e),encoding='utf-8')

# Structured records for sources whose body was empty/unauthorized or whose DNS lookup failed.
api_url='https://jcr.clarivate.com/api/jcr3/journalprofile/v1/journal-informationByIssnEssn'
api_sha=hashlib.sha256(b'').hexdigest()
api_attempts=[]
for issn in ['0951-8320','0888-3270','1270-9638']:
    fn=f'clarivate_api_{issn.replace("-","")}_401.txt'
    (RAW/fn).write_bytes(b'')
    api_attempts.append({'artifact':'raw/'+fn,'url':api_url,'http_status':401,'final_url':api_url,'access_time_local':'2026-10-03 (capture run; exact request timestamp unavailable in prior shell log)','request_method':'POST','request_parameter':{'issn':issn},'sha256':api_sha,'bytes':0,'interpretation':'Unauthorized response with empty body; no JCR quartile extracted.'})
records.extend(api_attempts)
cas_fail='fenqubiao_dns_failure.txt'
(RAW/cas_fail).write_text('URL: https://www.fenqubiao.com/\nObservation: DNS resolution failed during the audit; no response body or dated CAS partition record was obtained.\n',encoding='utf-8')
records.append({'artifact':'raw/'+cas_fail,'url':'https://www.fenqubiao.com/','http_status':'DNS_FAILURE','final_url':None,'access_time_local':'2026-10-03 (capture run; exact request timestamp unavailable in prior shell log)','sha256':sha256(RAW/cas_fail),'bytes':(RAW/cas_fail).stat().st_size,'interpretation':'No public CAS partition record was verified.'})

# Keep source status/URL facts explicit for copied captures. These are the statuses recorded by the capture run.
source_meta={
 'raw/tim_authors.html':('https://ieee-ims.org/publication/ieee-tim/information-authors',200,'https://ieee-ims.org/publication/ieee-tim/information-authors'),
 'raw/tim_templates.html':('https://ieee-ims.org/publication/ieee-tim/tim-paper-templates',200,'https://ieee-ims.org/publication/ieee-tim/tim-paper-templates'),
 'raw/tim_charge.pdf':('https://ieee-ims.org/files/ieeeims/2025-12/on-lineoverlengthpagechargeagreement-nov2025.pdf',200,'https://ieee-ims.org/files/ieeeims/2025-12/on-lineoverlengthpagechargeagreement-nov2025.pdf'),
 'raw/tim_landing.html':('https://ieee-ims.org/publication/ieee-transactions-instrumentation-and-measurement',200,'https://ieee-ims.org/publication/ieee-transactions-instrumentation-and-measurement'),
 'raw/trel_rs.html':('https://rs.ieee.org/publications/transactions-on-reliability.html',200,'https://rs.ieee.org/publications/transactions-on-reliability.html'),
 'raw/trel_review_policy.pdf':('https://rs.ieee.org/images/files/Publications/Trans_Reliability/IEEE%20TrR%20Review%20Policy_2026_519.pdf',200,'https://rs.ieee.org/images/files/Publications/Trans_Reliability/IEEE%20TrR%20Review%20Policy_2026_519.pdf'),
 'raw/trel_xplore_response.html':('https://www.ieee.org/publications/periodicals/transactions-on-reliability.html',202,'https://www.ieee.org/publications/periodicals/transactions-on-reliability.html'),
 'raw/taes_page.html':('https://ieee-aess.org/publications/taes',200,'https://ieee-aess.org/publications/taes'),
 'raw/taes_authors.html':('https://ieee-aess.org/publications/transactions-aes/author-information',200,'https://ieee-aess.org/publications/transactions-aes/author-information'),
 'raw/taes_template.zip':('https://confcats-web-assets.s3.amazonaws.com/ieeeaess/documents/TAES+Template.zip',200,'https://confcats-web-assets.s3.amazonaws.com/ieeeaess/documents/TAES+Template.zip'),
 'raw/ieee_general_peer_review.html':('https://journals.ieeeauthorcenter.ieee.org/submit-your-article-for-peer-review/about-the-peer-review-process/',200,'https://journals.ieeeauthorcenter.ieee.org/submit-your-article-for-peer-review/about-the-peer-review-process/'),
 'raw/cas_home.html':('https://www.cas.cn/',200,'https://www.cas.cn/'),
 'raw/clarivate_jcr_home.html':('https://jcr.clarivate.com/jcr/home',200,'https://jcr.clarivate.com/jcr/home'),
 'raw/clarivate_jcr_bundle.js':('https://jcr.clarivate.com/jcr/home (application bundle discovered during audit)',200,'https://jcr.clarivate.com/jcr/home'),
}
by={x['artifact']:x for x in records}
for art,(url,status,final) in source_meta.items():
    if art in by:
        by[art].update({'url':url,'http_status':status,'final_url':final,'access_time_local':by[art].get('capture_time_local')})

# Normalize HTML/PDF text for reviewable quote extraction. PDF text was already extracted by pdftotext in the capture run.
def html_text(path):
    if BeautifulSoup is None: return ''
    try:
        s=BeautifulSoup(path.read_bytes(),'html.parser')
        return '\n'.join(' '.join(x.get_text(' ',strip=True).split()) for x in s.find_all(['h1','h2','h3','h4','h5','p','li','td','th']))
    except Exception: return ''
for name in ['tim_authors.html','tim_templates.html','tim_landing.html','trel_rs.html','taes_page.html','taes_authors.html','ieee_general_peer_review.html','ieee_accessibility_guidance.html','cas_home.html','clarivate_jcr_home.html']:
    p=RAW/name
    if p.exists(): (EXT/(Path(name).stem+'_text.txt')).write_text(html_text(p),encoding='utf-8')
if (RAW/'trel_review_policy_extracted.txt').exists(): shutil.copy2(RAW/'trel_review_policy_extracted.txt',EXT/'trel_review_policy_text.txt')

# Exact excerpts selected from the normalized source texts; these avoid claiming fields not stated on the cited page.
quotes={
 'tim_authors':[
  'Please submit a single self-contained unencrypted PDF file no larger than 100 MB. Files larger than 100 MB will not be accepted.',
  'Authors are asked to submit their manuscript in IEEE double-column Transactions format. The minimum number of pages for regular papers is 5 pages. There is no maximum, although overlength charges apply. If your paper is less than 5 pages, you need to submit it as a short paper.',
  'include a no more than a 150-word abstract',
 ],
 'trel_rs':[
  'Each published article was reviewed by three independent reviewers using a single-anonymous peer review process',
  'Any paper shorter than five pages is likely to be rejected without evaluation unless it is well-written with solid contributions to advance reliability and related areas.',
  'The page limit of a manuscript is 15. A manuscript over 15 pages will be rejected without further review.',
  'Each submission must conform to the double column and single-spaced format of printed articles ... with all figures and tables embedded in the paper',
 ],
 'trel_policy':[
  'TRel requires each paper to be reviewed by AT LEAST TWO (2) independent reviewers with THREE (3) reviewers preferred by default.',
  'The page limit of a manuscript is 15. A manuscript over 15 pages will be rejected without further review.',
  'The font size should be 11-point.',
 ],
 'taes_authors':[
  'Contributions may be in the form of regular papers or correspondence items.',
  'Each published article is reviewed by a minimum of two independent reviewers using a single-anonymous peer-review process',
  'Overlength page charges are $200 per page for each printed page beyond ten for a regular paper or $200 per page for each printed page beyond six for a correspondence item.',
  'All IEEE journals require an Open Researcher and Contributor ID (ORCID) for all authors.',
  'Authors can submit supplementary materials including multimedia files, images, data sets, code and accompanying PDF documents. To aid reproducibility, authors are encouraged to submit all files necessary to recreate the results in the paper.',
 ],
 'ieee_peer':[
  'The most common types of peer review are single-anonymous, double-anonymous, and transparent peer review',
  'most IEEE publications use the single-anonymous format.',
 ],
 'ieee_accessibility':[
  'IEEE strives to provide an accessible web presence',
  'WCAG 2.0 Level A',
 ],
}
for key,qs in quotes.items():
    (EXT/(key+'_quotes.txt')).write_text('\n'.join('QUOTE: '+q for q in qs)+'\n',encoding='utf-8')

# Add human-readable source ledger.
for x in records:
    x.setdefault('access_time_local',x.get('capture_time_local'))
manifest={'created_at_local':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'timezone':'Asia/Shanghai','records':records}
(EV/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

readme=f'''# Venue rules evidence package (2026-10-03)\n\nThis directory is the auditable evidence package for `venue_rules_verified_20261003.md`. It contains copies of the official responses captured during the venue audit, normalized text extracts, exact quote selections, and a machine-readable `manifest.json`. Hashes are SHA-256 over the saved artifact bytes.\n\n## Interpretation boundary\n\n- IEEE venue rules are official publisher/society instructions and are usable as venue-specific submission constraints.\n- The general IEEE peer-review and accessibility pages are corroboration only. The accessibility page concerns general IEEE web accessibility guidance; it is not an article-PDF compliance rule.\n- Clarivate API attempts returned HTTP 401 with empty bodies, and no public dated CAS partition record was obtained. Therefore no current JCR/CAS Q1 claim is made for RESS, MSSP, or AST.\n- `trel_rs.html` says three independent reviewers for each published article; the separate 2026 review-policy PDF says at least two, with three preferred. Both statements are preserved and the difference is reported in the note.\n\n## Files\n\n- `raw/`: source captures and binary documents.\n- `extracts/`: normalized HTML/PDF text and exact quote selections.\n- `manifest.json`: URL, status, final URL, capture time, size, and SHA-256 for each artifact.\n\nThe package was written only under `work/paper/review/venue_rules_evidence_20261003/`.\n'''
(EV/'README.md').write_text(readme,encoding='utf-8')
print('wrote',EV)
print('records',len(records))
for x in records: print(x['artifact'],x['sha256'],x.get('http_status'))
