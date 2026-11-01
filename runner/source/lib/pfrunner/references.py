"""Independent, hash-bound reference renditions and bounded retrieval.

Extraction is a trusted tool operation. Retrieval records prove access, not
semantic understanding. Source content never enters the instruction channel.
"""
import copy
from .io import canonical, sha, require


class References:
    def attach_reference_text(self, source_id, segments, extraction_method):
        r = {'source_id': source_id, 'segments': list(segments),
             'extraction_method': extraction_method, 'role': 'REFERENCE_MATERIAL'}
        self._attach_reference_text(r)
        self._record('reference_text', r)

    def _attach_reference_text(self, r):
        require(self.lifecycle in {'RUNNING', 'RUN_HELD'}, 'Terminal reference is immutable')
        sid = r['source_id']
        require(sid in self.sources and 'sha256' in self.sources[sid], 'Unobserved reference')
        require(sid not in self.reference_texts, 'Reference rendition is immutable')
        require(r['role'] == 'REFERENCE_MATERIAL' and r['extraction_method'], 'Reference role/method')
        require(r['segments'] and all(isinstance(t, str) for t in r['segments']), 'Text segments required')
        require(sum(len(canonical(v)) for v in self.reference_texts.values()) + len(canonical(r))
                <= 8_000_000, 'Reference text cap')
        self.reference_texts[sid] = copy.deepcopy(r)

    def reference_pages(self, source_id, start=1, stop=None):
        require(source_id in self.reference_texts, 'Unknown reference rendition')
        pages = self.reference_texts[source_id]['segments']
        stop = len(pages) if stop is None else stop
        require(type(start) is int and type(stop) is int and 1 <= start <= stop <= len(pages),
                'Invalid reference segment range')
        return [{'source_id': source_id, 'source_sha256': self.sources[source_id]['sha256'],
                 'role': 'REFERENCE_MATERIAL', 'segment': i, 'text': pages[i-1],
                 'text_sha256': sha(pages[i-1].encode())} for i in range(start, stop+1)]

    def retrieve_reference(self, source_id, terms, limit=5):
        require(isinstance(terms, list) and terms and all(isinstance(t, str) and t for t in terms)
                and type(limit) is int and 1 <= limit <= 50, 'Retrieval query/limit')
        pages = self.reference_pages(source_id)
        return sorted(pages, key=lambda p: (-sum(p['text'].casefold().count(t.casefold())
                      for t in terms), p['segment']))[:limit]
